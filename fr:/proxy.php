<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: text/calendar; charset=utf-8');

$url = isset($_GET['url']) ? $_GET['url'] : '';

// Liste des domaines autorisés par sécurité
$allowed = array('booking.com', 'airbnb.fr', 'greengo.voyage');

$isValid = false;
foreach ($allowed as $domain) {
    if (strpos($url, $domain) !== false) {
        $isValid = true;
        break;
    }
}

if ($isValid && filter_var($url, FILTER_VALIDATE_URL)) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    $response = curl_exec($ch);
    curl_close($ch);
    echo $response;
} else {
    http_response_code(400);
    echo "URL non autorisée.";
}
?>