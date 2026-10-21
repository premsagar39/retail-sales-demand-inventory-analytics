# Data dictionary

SQL types, nullable attributes, primary keys and relationships are defined in `sql/schema.sql`. All pipeline output columns are specified in `src/schema.json`.

## stores

| Field | MySQL type |
|---|---|
| store_nbr | INT NOT NULL PRIMARY KEY |
| city | VARCHAR(100) |
| state | VARCHAR(100) |
| type | VARCHAR(10) |
| cluster | INT |

## families

| Field | MySQL type |
|---|---|
| family | VARCHAR(100) NOT NULL PRIMARY KEY |

## dates

| Field | MySQL type |
|---|---|
| date | DATE NOT NULL PRIMARY KEY |
| year | INT |
| month | VARCHAR(7) |
| weekday | INT |

## sales

| Field | MySQL type |
|---|---|
| id | BIGINT NOT NULL PRIMARY KEY |
| date | DATE NOT NULL |
| store_nbr | INT NOT NULL |
| family | VARCHAR(100) NOT NULL |
| sales | DOUBLE |
| onpromotion | DOUBLE |

## transactions

| Field | MySQL type |
|---|---|
| date | DATE NOT NULL |
| store_nbr | INT NOT NULL |
| transactions | BIGINT |

## holidays

| Field | MySQL type |
|---|---|
| event_id | INT NOT NULL PRIMARY KEY |
| date | DATE |
| type | VARCHAR(32) |
| locale | VARCHAR(32) |
| locale_name | VARCHAR(100) |
| description | VARCHAR(255) |
| transferred | VARCHAR(10) |
