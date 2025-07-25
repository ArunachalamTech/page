<?php
if (isset($_POST["newwpsafelink"])) {
    $id_parts = explode('_', $_POST["newwpsafelink"]);
    // echo json_encode($id_parts);
    $id = substr($id_parts[0], 6);
    $hash = substr($id_parts[0], 0, 6);

    // API call
    $curl = curl_init();
    $postData = json_encode(array("id" => $id, "hash" => $hash)); // Use json_encode to format the data correctly

    curl_setopt_array($curl, array(
        CURLOPT_URL => 'https://krfile2link-3-c391ce1d6289.herokuapp.com/api/file',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING => '',
        CURLOPT_MAXREDIRS => 10,
        CURLOPT_TIMEOUT => 0,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
        CURLOPT_CUSTOMREQUEST => 'POST',
        CURLOPT_POSTFIELDS => $postData, // Corrected data formatting
        CURLOPT_HTTPHEADER => array(
            'Content-Type: application/json'
        ),
    ));

    $response = curl_exec($curl);
    curl_close($curl);

    $res = json_decode($response, true); // Decoding the JSON response to an array

    // Check if 'status' exists and display the error message
    if (isset($res["status"]) && $res["status"] == "success") { ?>
        <style>
            .xdigital-blue {
                background: #5a7ce2;
                background: -moz-linear-gradient(-45deg, #5a7ce2 0, #8283e8 50%, #6624c8 51%, #565bd8 71%, #575cdb 100%);
                background: -webkit-linear-gradient(-45deg, #5a7ce2 0, #8283e8 50%, #6624c8 51%, #565bd8 71%, #575cdb 100%);
                background: linear-gradient(135deg, #5a7ce2 0, #8283e8 50%, #6624c8 51%, #565bd8 71%, #575cdb 100%);
                background-size: 400% 400%;
                -webkit-animation: 3s infinite AnimationName;
                -moz-animation: 3s infinite AnimationName;
                animation: 3s infinite AnimationName;
                border: none;
            }

            .xdigital-btn {
                border-radius: 100px;
                margin: 0 auto;
                font-size: 12px;
                color: #fff !important;
                font-weight: 505;
                letter-spacing: 1px;
                cursor: pointer;
                padding: 8px 40px !important;
                text-shadow: 1px 1px 1px rgba(0, 0, 0, .14);
                text-transform: uppercase;
                box-shadow: 0 4px 9px 0 rgba(0, 0, 0, .2);
                transition: color .15s ease-in-out, background-color .15s ease-in-out, border-color .15s ease-in-out, box-shadow .15s ease-in-out;
            }

            /* Example keyframes animation, ensure to replace 'AnimationName' */
            @keyframes AnimationName {
                0% {
                    background-position: 0% 50%;
                }

                100% {
                    background-position: 100% 50%;
                }
            }
        </style>
        <!-- ad code here -->

        <center>
            <div>
                <h3>File Info :</h3>
                <p>File Name : <?php echo $res["file_name"]; ?></p>
                <p>File Size : <?php echo $res["file_size"]; ?></p>
            </div>
            <!---- ADS Code Here ---->
            <center>
                <!-- AdOto - Ad Display Code -->
                <div id="adm-container-7025"></div>
                <script data-cfasync="false" async type="text/javascript" src="//adoto.net/dashboard/display/items.php?7025&2284&300&250&4&0&0"></script>
                <script data-cfasync="false" type="text/javascript" src="//adoto.net/dashboard/display/serve.js"></script>
                <!-- AdOto - Ad Display Code -->
            </center>
            <!---- ADS Code Here ---->
            <div id="link">
                <h4> Please wait <span id="xdigital-time" style="color:#c91212;">10</span> Seconds</h4>
            </div>
            <!---- ADS Code Here ---->
            <center> 
            <!-- AdOto - Ad Display Code -->
<div id="adm-container-7083"></div><script data-cfasync="false" async type="text/javascript" src="//adoto.net/dashboard/display/items.php?7083&2284&300&250&4&0&0"></script><script data-cfasync="false" type="text/javascript" src="//adoto.net/dashboard/display/serve.js"></script>
<!-- AdOto - Ad Display Code -->

            </center>
            <!---- ADS Code Here ---->
            <div id="xdigital-generate" style="display:none;">
                <center>
                    <h4>Scroll down &amp; click on <b><span style="color:#c91212;">OPEN - Continue</span></b> button for your destination link</h4>
                </center>
            </div>
            <!---- ADS Code Here ---->
            <center>
                <!-- AdOto - Ad Display Code -->
                <div id="adm-container-7026"></div>
                <script data-cfasync="false" async type="text/javascript" src="//adoto.net/dashboard/display/items.php?7026&2284&300&250&4&0&0"></script>
                <script data-cfasync="false" type="text/javascript" src="//adoto.net/dashboard/display/serve.js"></script>
                <!-- AdOto - Ad Display Code -->
            </center>
            <!---- ADS Code Here ---->
        </center>

    <?php } elseif (isset($res["status"]) && $res["status"] == "error") { ?>
        <h3>Something wrong; file is not working </h3>
        <?php echo htmlspecialchars($res["message"]); // Using htmlspecialchars to avoid XSS 
        ?>
    <?php } else { ?>
        <h3>Something went wrong; file is not working </h3>
<?php }
}
?>