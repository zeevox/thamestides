<?php
header('Content-Type: application/json');

$start_time = microtime(true);

$db = new SQLite3("../thamestides.db", SQLITE3_OPEN_READONLY);

// get valid column names for predictions (prevent SQL injection)
$predictions = array();
$predictions_query = $db->query("PRAGMA table_info(predictions);");
while ($table = $predictions_query->fetchArray(SQLITE3_ASSOC)) { $predictions[] = $table['name']; }
unset($predictions[0]); // time is our primary column but it is not a station!

// get valid column names for readings (prevent SQL injection)
$readings = array();
$readings_query = $db->query("PRAGMA table_info(readings);");
while ($table = $readings_query->fetchArray(SQLITE3_ASSOC)) { $readings[] = $table['name']; }
unset($readings[0]); // time is our primary column but it is not a station!

function error(string $error_message, int $http_error_code) {
    http_response_code($http_error_code);
    $error = array(
        "status_code" => $http_error_code,
        "message" => $error_message,
        "input" => $_GET,
    );
    echo json_encode($error, JSON_PRETTY_PRINT);
    exit;
}

$results = array();

if (sizeof($_GET) == 0) {
    error("No data was requested; check your url", 204);
}

$get_predictions = isset($_GET["predictions"]);
$get_readings = isset($_GET["readings"]);

if ($get_predictions or $get_readings) {
    // you can use the `stations` parameter with a comma-separated list (no spaces)
    if (isset($_GET["stations"])) {
        if ($_GET["stations"] == "all") {
            // if we are requesting all the stations we take the two lists of valid stations, combine them and remove duplicates
            $column_names = array_unique(array_merge($readings, $predictions));
        } else {
            // otherwise we split the string into an array delimiting by comma
            $column_names = explode(",", $_GET["stations"]);
        }
    // or use the `station` parameter for a single tidal station
    } else if (isset($_GET["station"])) {
        $column_names = array(htmlspecialchars($_GET["station"]));
    } else {
        error("No station name(s) included in request. If you are certain that you need all the stations, set `stations=all`", 400);
    }

    // number of measurements to retrieve from the database
    if (isset($_GET["last_n"])) {
        $last_n = intval($_GET["last_n"]); // if n is not an integer (e.g. string) this returns zero
        // 1440 readings is one day's worth of minutely readings. Let's not overload the server. Filter by time or if absolutely necessary make individual requests.
        if ($last_n > 1440) error("Request received for $last_n readings. The maximum is 1440 readings per request.", 400);
        if (!($last_n > 0)) error("Invalid value for last_n: $last_n", 400);
    } else {
        $last_n = 1;
    }

    if (!is_null($column_names)) {
        foreach ($column_names as $column_name) {
            // verify that the submitted station names are valid
            $valid_reading_station = in_array($column_name, $readings) and $get_readings;
            $valid_prediction_station = in_array($column_name, $predictions) and $get_predictions;
            if (!$valid_reading_station and !$valid_prediction_station) error("Invalid station name: $column_name", 400);

            if ($valid_reading_station) {
                $readings_result = array();

                // option to filter out null readings where the gauge was offline
                if (isset($_GET["filter_non_null"])) $filter_non_null = "WHERE $column_name IS NOT NULL"; else $filter_non_null = "";

                // The recommended way to do a SQLite3 query is to use a statement.
                $statement_readings = $db->prepare("SELECT time, $column_name FROM readings $filter_non_null ORDER BY time DESC LIMIT $last_n");
                if ($statement_readings) {
                    $result = $statement_readings -> execute();

                    // iterate over the rows of the fetched data, and add it to a array of this specific column
                    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
                        $readings_result[$row["time"]] = $row[$column_name];
                    }

                    // close the statement, save some RAM
                    $statement_readings->close();

                    // sort the output by timestamp
                    ksort($readings_result);

                    // add this specific column's array to the final total output array
                    $results[$column_name]["readings"] = $readings_result;

                    unset($readings_result);
                } else {
                    error("Error fetching readings for $column_name", 500);
                }
            }

            if ($valid_prediction_station) {
                $predictions_result = array();

                // in order to filter for only future predictions
                $timestamp = intval(time());

                // The recommended way to do a SQLite3 query is to use a statement.
                $statement_predictions = $db->prepare("SELECT time, $column_name FROM main.predictions WHERE time >= $timestamp AND $column_name IS NOT NULL ORDER BY time DESC LIMIT 2");
                if ($statement_predictions) {
                    $result = $statement_predictions -> execute();

                    // iterate over the rows of the fetched data, and add it to a array of this specific column
                    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
                        $predictions_result[$row["time"]] = $row[$column_name];
                    }

                    // close the statement, save some RAM
                    $statement_predictions->close();

                    // sort the output by timestamp
                    ksort($predictions_result);

                    if (!empty($predictions_result)) {
                        // add this specific column's array to the final total output array
                        $results[$column_name]["predictions"] = $predictions_result;
                    }

                    unset($predictions_result);
                } else {
                    error("Error fetching predictions for $column_name", 500);
                }
            }

            if (isset($results[$column_name])) {
                $results[$column_name]["units"] = "m";
            }
        }
    }

} else {
    error("Please select one of `predictions` or `readings`", 400);
}

// to see how long it took to gather the data
$results["execution_time"] = microtime(true) - $start_time;
$results["status_code"] = "200";

echo json_encode($results, JSON_PRETTY_PRINT);

?>
