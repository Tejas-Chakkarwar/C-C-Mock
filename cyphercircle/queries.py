"""All Cypher used by the Milestone 0 vertical slice."""

COUNT_ALL_NODES = """
MATCH (n)
RETURN count(n) AS nodes
""".strip()

CREATE_USER_USERNAME_CONSTRAINT = """
CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE
""".strip()

CREATE_USER_EMAIL_CONSTRAINT = """
CREATE CONSTRAINT user_email_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.email IS UNIQUE
""".strip()

CREATE_USER_SOURCE_ID_CONSTRAINT = """
CREATE CONSTRAINT user_source_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.source_id IS UNIQUE
""".strip()

CREATE_CIRCLE_ID_CONSTRAINT = """
CREATE CONSTRAINT circle_id_unique IF NOT EXISTS
FOR (c:Circle) REQUIRE c.circle_id IS UNIQUE
""".strip()

CREATE_USER_NAME_TEXT_INDEX = """
CREATE TEXT INDEX user_name_lc_text IF NOT EXISTS
FOR (u:User) ON (u.name_lc)
""".strip()

CREATE_USER_USERNAME_TEXT_INDEX = """
CREATE TEXT INDEX user_username_text IF NOT EXISTS
FOR (u:User) ON (u.username)
""".strip()

LOAD_CIRCLES = """
UNWIND $rows AS row
MERGE (c:Circle {circle_id: row.circle_id})
SET c.name = row.name,
    c.source_label = row.source_label,
    c.owner_source_id = row.owner_source_id,
    c.source = 'snap',
    c.load_token = $load_token
RETURN count(*) AS loaded
""".strip()

LOAD_USERS = """
UNWIND $rows AS row
MERGE (u:User {source_id: row.source_id})
SET u.username = row.username,
    u.email = row.email,
    u.name = row.name,
    u.name_lc = row.name_lc,
    u.password_hash = row.password_hash,
    u.bio = row.bio,
    u.location = row.location,
    u.joined_at = datetime(row.joined_at),
    u.source = 'snap',
    u.load_token = $load_token
RETURN count(*) AS loaded
""".strip()

LOAD_MEMBERSHIPS = """
UNWIND $rows AS row
MATCH (u:User {source_id: row.source_id})
MATCH (c:Circle {circle_id: row.circle_id, source: 'snap'})
MERGE (u)-[r:IN_CIRCLE]->(c)
SET r.load_token = $load_token
RETURN count(*) AS loaded
""".strip()

LOAD_FOLLOWS = """
UNWIND $rows AS row
MATCH (a:User {source_id: row.src})
MATCH (b:User {source_id: row.dst})
MERGE (a)-[r:FOLLOWS]->(b)
ON CREATE SET r.since = datetime(row.since)
SET r.load_token = $load_token
RETURN count(*) AS loaded
""".strip()

VERIFY_COUNTS = """
RETURN count { (:User) } AS users,
       count { (:Circle) } AS circles,
       count { ()-[:FOLLOWS]->() } AS follows,
       count { ()-[:IN_CIRCLE]->() } AS memberships
""".strip()

VERIFY_DATASET_COUNTS = """
MATCH (u:User {source: 'snap'})
WITH count(u) AS users
CALL () {
  MATCH (c:Circle)
  WHERE c.source = 'snap'
  RETURN count(c) AS circles
}
CALL () {
  MATCH (a:User {source: 'snap'})-[:FOLLOWS]->(b:User {source: 'snap'})
  RETURN count(*) AS follows
}
CALL () {
  MATCH (a:User {source: 'snap'})-[:IN_CIRCLE]->(c:Circle {source: 'snap'})
  RETURN count(*) AS memberships
}
RETURN users, circles, follows, memberships
""".strip()

MARK_EXISTING_CIRCLES_AS_SNAP = """
MATCH (c:Circle)
WHERE c.source IS NULL
SET c.source = 'snap'
RETURN count(c) AS marked
""".strip()

AWAIT_INDEXES = """
CALL db.awaitIndexes()
""".strip()

CLEAR_LOAD_TOKEN = """
WITH $load_token AS load_token
CALL (load_token) {
  MATCH ()-[r]-()
  WHERE r.load_token = load_token
  DELETE r
  RETURN count(*) AS deleted_relationships
}
CALL (load_token) {
  MATCH (n)
  WHERE n.load_token = load_token AND NOT (n)--()
  DELETE n
  RETURN count(*) AS deleted_nodes
}
RETURN deleted_relationships, deleted_nodes
""".strip()

FINALIZE_LOAD = """
WITH $load_token AS load_token
CALL (load_token) {
  MATCH (n)
  WHERE n.load_token = load_token
  REMOVE n.load_token
  RETURN count(n) AS nodes
}
CALL (load_token) {
  MATCH ()-[r]-()
  WHERE r.load_token = load_token
  REMOVE r.load_token
  RETURN count(r) AS relationships
}
RETURN nodes, relationships
""".strip()

CREATE_USER = """
CREATE (u:User {
  username: $username,
  email: $email,
  name: $name,
  name_lc: toLower($name),
  password_hash: $password_hash,
  bio: $bio,
  location: $location,
  joined_at: datetime($joined_at),
  source: 'app'
})
RETURN u.username AS username, u.name AS name
""".strip()

CREATE_SLICE_USER = """
CREATE (u:User {
  username: $username,
  email: $email,
  name: $name,
  name_lc: toLower($name),
  password_hash: $password_hash,
  bio: $bio,
  location: $location,
  joined_at: datetime($joined_at),
  source: 'slice_check'
})
RETURN u.username AS username, u.name AS name
""".strip()

GET_AUTH_BY_USERNAME = """
MATCH (u:User {username: $username})
RETURN u.password_hash AS password_hash, u.name AS name
""".strip()

FOLLOW_USER = """
MATCH (me:User {username: $me}), (target:User {username: $target})
WHERE me <> target
MERGE (me)-[r:FOLLOWS]->(target)
ON CREATE SET r.since = datetime()
RETURN r.since AS since
""".strip()

RECOMMEND_BY_NETWORK = """
MATCH (me:User {username: $username})-[:FOLLOWS]->(mid:User)-[:FOLLOWS]->(rec:User)
WHERE rec <> me AND NOT (me)-[:FOLLOWS]->(rec)
WITH rec, mid ORDER BY mid.username ASC
WITH rec, count(DISTINCT mid) AS score, collect(DISTINCT mid.username)[..3] AS via
RETURN rec.username AS username,
       rec.name AS name,
       rec.location AS location,
       count { (:User)-[:FOLLOWS]->(rec) } AS followers,
       score,
       via
ORDER BY score DESC, followers DESC, username ASC
LIMIT $limit
""".strip()

DELETE_SLICE_USER = """
MATCH (u:User {username: $username, source: 'slice_check'})
DETACH DELETE u
""".strip()


