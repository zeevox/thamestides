<?php

/**
 * Output a JSON response and exit the program
 *
 * @param int $code the HTTP response code of the program
 * @param $results array|string array with the response data OR string with an error message
 */
function output(int $code, $results) {
    // Remove any existing HTTP headers
    header_remove();

    // Set the actual response code
    http_response_code($code);

    // Enable caching for up to a minute
    header("Cache-Control: no-transform,public,max-age=60,s-maxage=60");

    // Inform that this is JSON
    header('Content-Type: application/json');

    // Set the status to reflect the HTTP response code
    $status = array(
        200 => '200 OK',
        204 => '206 Partial Content',
        400 => '400 Bad Request',
        422 => '422 Unprocessable Entity',
        500 => '500 Internal Server Error',
        503 => '503 Service Unavailable',
    );
    header('Status: '.$status[$code]);

    // If the "result" that has been passed is a single string, i.e. error message, wrap it
    if (is_string($results)) $results = array("message" => $results);

    // Add the status code to the response content itself
    $results["status_code"] = $code;

    // If there has been an error, output the received input for debugging purposes
    if ($code != 200) $results["input"] = filter_input_array(INPUT_GET);

    // Pretty print the output
    print_r(json_encode((object) $results, JSON_PRETTY_PRINT));

    // Do not run any further
    exit();
}

/**
 * Query the database to get a list of valid station names to prevent SQL injection
 *
 * @param $db SQLite3 database to fetch column names from
 * @param string $table_name the name of the table to search within
 * @return array list of valid station names
 */
function get_valid_stations($db, string $table_name) {
    $valid_stations = array();
    $query = $db->query("PRAGMA table_info($table_name);");

    // each call to fetchArray() returns an array of a single row of the output
    // so to get all the rows that the query fetched, we keep calling fetchArray() until it no longer returns an array
    while ($table_name = $query->fetchArray(SQLITE3_ASSOC)) { $valid_stations[] = $table_name['name']; }

    // we make the assumption here that the first column in the database must be the timestamp primary key
    // it is a valid column, but not a valid station name, so we remove it from the list of valid station names
    unset($valid_stations[0]);

    return $valid_stations;
}

// operating in UTC is the easiest way to avoid timezone confusion
// plus the database stores the Unix timestamps in UTC
date_default_timezone_set("UTC");

$program_start_time = microtime(true);

// the database is located in the root project folder, thus go up a level to access it
define("DB_NAME", "../thamestides.db");

// instantiate a read-only connection to the database, both for safety's sake
// and because we do not plan on writing anything into it
$db = new SQLite3(DB_NAME, SQLITE3_OPEN_READONLY);

$predictions = get_valid_stations($db, "predictions");
$readings = get_valid_stations($db, "readings");

// Instantiate an empty results array into which we place the fetched data
$results = array();

if (count(filter_input_array(INPUT_GET)) == 0) {
    output(206, "No data was requested; check your url");
}

$get_predictions = filter_has_var(INPUT_GET, "predictions");
$get_readings = filter_has_var(INPUT_GET, "readings");

if ($get_predictions || $get_readings) {
    // you can use the `stations` parameter with a comma-separated list (no spaces)
    if (filter_has_var(INPUT_GET, "stations")) {
        $stations = filter_input(INPUT_GET, "stations");
        if ($stations == "all") {
            // if we are requesting all the stations we take the two lists of valid stations, combine them and remove duplicates
            $column_names = array_unique(array_merge($readings, $predictions));
        } else {
            // otherwise we split the string into an array delimiting by comma
            $column_names = explode(",", $stations);
        }
    // or use the `station` parameter for a single tidal station
    } else if (filter_has_var(INPUT_GET, "station")) {
        $column_names = array(htmlspecialchars(filter_input(INPUT_GET, "station")));
    } else {
        output(400, "No station name(s) included in request. If you are certain that you need all the stations, set `stations=all`");
    }

    // number of measurements to retrieve from the database
    if (filter_has_var(INPUT_GET, "last_n")) {
        $last_n = (int) filter_input(INPUT_GET, "last_n"); // if n is not an integer (e.g. string) this returns zero
        // 1440 readings is one day's worth of minutely readings. Let's not overload the server. Filter by time or if absolutely necessary make individual requests.
        if ($last_n > 1440) output(422, "Request received for $last_n readings. The maximum is 1440 readings per request.");
        if (!($last_n > 0)) output(422, "Invalid value for last_n: $last_n");
    } else {
        $last_n = 1;
    }

    $end_time = (int) time();
    $start_time = $end_time - (60 * 60 * 24);
    $start_predictions = $end_time;
    $end_predictions = $end_time + (60 * 60 * 24);
    if (filter_has_var(INPUT_GET, "start")
        && filter_has_var(INPUT_GET, "end")) {
        $start_time = strtotime(filter_input(INPUT_GET, "start"));
        $end_time = strtotime(filter_input(INPUT_GET, "end"));
        $start_predictions = $start_time;
        $end_predictions = $end_time;
        if (!filter_has_var(INPUT_GET, "last_n")) $last_n = 1440;
    } else if (filter_has_var(INPUT_GET, "start")
        xor filter_has_var(INPUT_GET, "end")) {
        output(422, "Please set both `start` and `end` or neither");
    }


    if (!(($column_names) === null)) {
        foreach ($column_names as $column_name) {
            // verify that the submitted station names are valid
            $valid_reading_station = in_array($column_name, $readings) && $get_readings;
            $valid_prediction_station = in_array($column_name, $predictions) && $get_predictions;
            if (!$valid_reading_station && !$valid_prediction_station) output(422, "Invalid station name: $column_name");

            if ($valid_reading_station) {
                $readings_result = array();

                // option to filter out null readings where the gauge was offline
                if (filter_has_var(INPUT_GET, "filter_non_null"))
                    $filter_non_null = "WHERE $column_name IS NOT NULL"; else $filter_non_null = "WHERE ";

                // The recommended way to do a SQLite3 query is to use a statement.
                $statement_readings = $db->prepare("
                    SELECT time, $column_name
                    FROM readings
                    $filter_non_null time >= $start_time AND time <= $end_time
                    ORDER BY time
                    DESC
                    LIMIT $last_n
                ");

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

                    if (!empty($readings_result)) {
                        // add this specific column's array to the final total output array
                        $results[$column_name]["readings"] = $readings_result;
                    }

                    unset($readings_result);
                } else {
                    output(503, "Error fetching readings for $column_name");
                }
            }

            if ($valid_prediction_station) {
                $predictions_result = array();

                // The recommended way to do a SQLite3 query is to use a statement.
                $statement_predictions = $db->prepare("
                    SELECT time, $column_name
                    FROM main.predictions
                    WHERE time >= $start_predictions AND time <= $end_predictions
                      AND $column_name IS NOT NULL
                    ORDER BY time
                    DESC
                    LIMIT $last_n
                ");
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
                    output(503, "Error fetching predictions for $column_name");
                }
            }

            if (isset($results[$column_name])) {
                $results[$column_name]["units"] = "m";
            }
        }
    }

} else {
    output(400, "Please select one of `predictions` or `readings`");
}

// to see how long it took to gather the data
$results["execution_time"] = microtime(true) - $program_start_time;

output(200, $results);

?>
