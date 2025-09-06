import pandas as pd
import networkx as nx
from datetime import timedelta
from typing import Tuple

# ----------------------------
# Config
# ----------------------------
WINDOW_DAYS = 14 # ±14 days window relative to positive test date
DATE_FMT = "%Y-%m-%d"

def _read_csv(transfers_path: str, microbiology_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    tf = pd.read_csv(transfers_path, dtype=str)
    mc = pd.read_csv(microbiology_path, dtype=str)

    # Parse dates
    tf['ward_in_time'] = pd.to_datetime(tf['ward_in_time']).dt.normalize()
    tf['ward_out_time'] = pd.to_datetime(tf['ward_out_time']).dt.normalize()
    mc['collection_date'] = pd.to_datetime(mc['collection_date']).dt.normalize()

    # Basic cleaning
    tf = tf.dropna(subset=['patient_id', 'location', 'ward_in_time', 'ward_out_time'])
    mc = mc.dropna(subset=['patient_id', 'infection', 'result', 'collection_date'])

    return tf, mc

def _compute_positive_index(mc: pd.DataFrame) -> pd.DataFrame:
    # Finds first positive date per (patient_id, infection)
    positives = mc[mc['result'].str.lower() == 'positive'].copy()
    if positives.empty:
        return positives
    earliest = (
        positives.sort_values('collection_date')
        .groupby(['patient_id', 'infection'], as_index=False)
        .first()
    )
    earliest.rename(columns={'collection_date': 'positive_date'}, inplace=True)
    earliest['win_start'] = earliest['positive_date'] - pd.Timedelta(days=WINDOW_DAYS)
    earliest['win_end'] = earliest['positive_date'] + pd.Timedelta(days=WINDOW_DAYS)
    return earliest

def _expand_transfers_to_days(tf: pd.DataFrame, date_min: pd.Timestamp, date_max: pd.Timestamp) -> pd.DataFrame:
    """
    Expand transfers into per-day presence rows within [date_min, date_max].
    Columns: patient_id, date, location
    """
    tf2 = tf.copy()
    # Clip intervals to the allowed date range
    tf2['start'] = tf2['ward_in_time'].clip(lower=date_min, upper=date_max)
    tf2['end'] = tf2['ward_out_time'].clip(lower=date_min, upper=date_max)
    tf2 = tf2[tf2['end'] >= tf2['start']]

    # Create per-day date ranges and explode into separate rows
    tf2['date_range'] = tf2.apply(lambda r: pd.date_range(r['start'], r['end'], freq='D'), axis=1)
    exploded = tf2[['patient_id', 'location', 'date_range']].explode('date_range').rename(columns={'date_range': 'date'})
    exploded['date'] = exploded['date'].dt.normalize()
    return exploded

def _build_contacts_for_infection(presence: pd.DataFrame, pos_idx: pd.DataFrame, infection: str) -> pd.DataFrame:
    """Return contact edges (u, v, date, location) among positives for a given infection."""
    p = pos_idx[pos_idx['infection'] == infection].copy()
    if p.empty:
        return pd.DataFrame(columns=['u', 'v', 'date', 'location'])

    # Keep only presence rows for patients in this infection and within their window
    pres = presence.merge(p[['patient_id', 'win_start', 'win_end']], on='patient_id', how='inner')
    pres = pres[(pres['date'] >= pres['win_start']) & (pres['date'] <= pres['win_end'])]

    # Self-join on (date, location) to find co-presence pairs
    left = pres.rename(columns={'patient_id': 'u'})
    right = pres.rename(columns={'patient_id': 'v'})
    pairs = left.merge(right, on=['date', 'location'])

    # Remove self-pairs and make undirected unique pairs (u < v lexicographically)
    pairs = pairs[pairs['u'] != pairs['v']]
    pairs['a'] = pairs[['u', 'v']].min(axis=1)
    pairs['b'] = pairs[['u', 'v']].max(axis=1)
    pairs = pairs.drop_duplicates(subset=['a', 'b', 'date', 'location'])

    return pairs[['a', 'b', 'date', 'location']].rename(columns={'a': 'u', 'b': 'v'})

def detect_clusters(transfers_path: str, microbiology_path: str):
    tf, mc = _read_csv(transfers_path, microbiology_path)
    pos_idx = _compute_positive_index(mc)

    if pos_idx.empty:
        return {
            'clusters': [],
            'stats': {
                'infections': [],
                'total_clusters': 0,
                'patients_positive': 0
            }
        }

    # Limit expansion to relevant time horizon only
    date_min = (pos_idx['win_start'].min()).normalize()
    date_max = (pos_idx['win_end'].max()).normalize()

    presence = _expand_transfers_to_days(tf, date_min, date_max)

    clusters_all = []
    cluster_counter = 1

    for infection in sorted(pos_idx['infection'].unique()):
        edges = _build_contacts_for_infection(presence, pos_idx, infection)

        # Build graph among positive patients for this infection
        G = nx.Graph()
        pts = pos_idx[pos_idx['infection'] == infection]['patient_id'].unique().tolist()
        G.add_nodes_from(pts)

        # Edge weight: number of distinct contact days (or contact events)
        if not edges.empty:
            w = (
            edges.groupby(['u', 'v'])
            .size()
            .reset_index(name='contact_events')
            )
            for _, row in w.iterrows():
                G.add_edge(row['u'], row['v'], contact_events=int(row['contact_events']))

        # Connected components with size >= 2
        for comp in nx.connected_components(G):
            if len(comp) < 2:
                continue
            members = sorted(list(comp))
            sub = G.subgraph(members)
            # Metrics
            pos_sub = pos_idx[(pos_idx['infection'] == infection) & (pos_idx['patient_id'].isin(members))]
            first_pos = pos_sub['positive_date'].min()
            last_pos = pos_sub['positive_date'].max()
            timespan_days = int((last_pos - first_pos).days)
            contact_edges = sub.number_of_edges()
            contact_events = int(sum(d.get('contact_events', 0) for _, _, d in sub.edges(data=True)))

            # Locations involved (from edges -> dates/locations)
            locs = set()
            if not edges.empty:
                elocs = edges[(edges['u'].isin(members)) & (edges['v'].isin(members))]
                locs = set(elocs['location'].unique().tolist())

            clusters_all.append({
            'cluster_id': cluster_counter,
            'infection': infection,
            'size': len(members),
            'members': members,
            'first_positive': first_pos.strftime(DATE_FMT),
            'last_positive': last_pos.strftime(DATE_FMT),
            'timespan_days': timespan_days,
            'locations': sorted(list(locs)),
            'contact_edges': contact_edges,
            'contact_events': contact_events,
            })
            cluster_counter += 1
    
    grouped = {}
    for c in clusters_all:
        grouped.setdefault(c['infection'], []).append(c)
    infections = sorted({c['infection'] for c in clusters_all})
    return {
        "clusters": grouped,
        "stats": {
            'infections': infections,
            'total_clusters': len(clusters_all),
            'patients_positive': int(pos_idx['patient_id'].nunique())
        }
    }

def build_ward_summary(clusters_by_infection: dict):
    ward_summary = {}
    for infection, groups in clusters_by_infection.items():
        for cluster in groups:
            for loc in cluster["locations"]:
                ward_summary.setdefault(loc, {}).setdefault(infection, 0)
                ward_summary[loc][infection] += cluster["size"]
    return ward_summary
    