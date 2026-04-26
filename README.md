# Tables Meta Data

## global_data.csv
| Column Name        | Type    | Description |
|--------------------|---------|-------------|
| stop_id            | integer | Unique identifier of the physical stop (shared across all routes serving this stop) |
| makat              | integer | Route identifier |
| route_short_name   | string  | Public-facing route number or label (e.g., "77", "5א") |
| direction          | integer | Direction identifier of the route variant (e.g., 1/2, 3 for cycle route) |
| agency_name        | string  | Name of the public transport operator (e.g., אגד, סופרבוס) |
| stop_name          | string  | Name of the stop as shown to passengers |
| city_name          | string  | City or locality where the stop is located |

## route_by_cuty.csv
| Column Name        | Type    | Description |
|--------------------|---------|-------------|
| city_name          | string  | City or locality where the route operates (at least partially; may not reflect full route coverage) |
| makat              | integer | Route identifier |
| route_short_name   | string  | Public-facing route number or label (e.g., "77", "5א") |
| direction          | integer | Direction identifier of the route variant (e.g., 1/2, 3 for cycle route) |
| agency_name        | string  | Name of the public transport operator (e.g., אגד, סופרבוס) |

## stops_by_city.csv
| Column Name | Type    | Description |
|-------------|---------|-------------|
| city_name   | string  | City or locality where the stop is located (administrative assignment; may not reflect exact municipal boundaries) |
| stop_name   | string  | Name of the stop as presented to passengers |
| stop_id     | integer | Unique identifier of the stop (should be stable across the dataset and used for joins with other tables) |
