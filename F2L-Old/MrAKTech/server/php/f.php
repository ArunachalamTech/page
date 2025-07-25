<?php
if (isset($_POST["newwpsafelink"])) {

// echo json_encode($id_parts);

$CLOUDFLARE_URLS = [
    ".tg-x-server1.workers.dev/", 
    ".tg-x-server2.workers.dev/",
    ".tg-x-server3.workers.dev/", 
    ".tg-x-server4.workers.dev/", 
    ".tg-x-server5.workers.dev/"
];
$random_key = array_rand($CLOUDFLARE_URLS);

$id_parts = explode('_', $_POST["newwpsafelink"]);
if ($id_parts[1] == "dl" || $id_parts[1] == "DLServer0") {
    $urlx = "https://www" . $CLOUDFLARE_URLS[$random_key]."v2/".$id_parts[0];
    $button = "Click to Download";
} elseif ($id_parts[1] == "DLServer1") {
    $urlx = "https://dlserver1" . $CLOUDFLARE_URLS[$random_key]."stream/".substr($id_parts[0], 6);
    $button = "Click to Download Server1";
} elseif ($id_parts[1] == "DLServer2") {
    $urlx = "https://www" . $CLOUDFLARE_URLS[$random_key]."v3/".$id_parts[0];
    $button = "Click to Download Server2";
} elseif ($id_parts[1] == "tg") {
    $urlx = "https://telegram.me/FileAccessV4Bot?start=download_".substr($id_parts[0], 6);
    $button = "Open in Telegram";
} else {
    $urlx = "https://telegram.me/MrAK_BotZ";
    $button = "Invalid ID";
}
?>

<center>
<!-- AdOto - Ad Display Code -->
<div id="adm-container-7027"></div><script data-cfasync="false" async type="text/javascript" src="//adoto.net/dashboard/display/items.php?7027&2284&300&250&4&0&0"></script><script data-cfasync="false" type="text/javascript" src="//adoto.net/dashboard/display/serve.js"></script>
<!-- AdOto - Ad Display Code -->

<div id="xdigital" style="display:none;">
    <a href="<?php echo $urlx; ?>"  rel="nofollow" style="text-decoration: none; text-decoration: none;">
    <button id="xdigital"  class="xdigital-btn xdigital-blue" rel="noopener nofollow" ><?php echo $button; ?></button></a>
</div>
<!-- AdOto - Ad Display Code -->
<div id="adm-container-7084"></div><script data-cfasync="false" async type="text/javascript" src="//adoto.net/dashboard/display/items.php?7084&2284&300&250&4&0&0"></script><script data-cfasync="false" type="text/javascript" src="//adoto.net/dashboard/display/serve.js"></script>
<!-- AdOto - Ad Display Code -->
</center>
<script type="text/javascript"> 
    window.onload = function() {
        document.getElementById('xdigital-snp').style.display = 'none';
    };
    var count = 10;
    var counter = setInterval(timer, 1600);
    function timer() {
        count = count - 1;
        if (count <= 0) { 
            document.getElementById('link').style.display = 'none';
            document.getElementById('xdigital-generate').style.display = 'block';
            document.getElementById('xdigital').style.display = 'block';
            clearInterval(counter);
            return;
        }
        document.getElementById("xdigital-time").innerHTML = count;
    }
</script>
<?php
}
?>