<?php
// Altawakol Cables — RFQ handler for GoDaddy cPanel (PHP mail()).
// 1. Set $to to the inbox that answers quotations. 2. Set $from to an address on your domain (GoDaddy rejects foreign senders).
$to   = 'sales@altawakolcables.com';
$from = 'website@altawakolcables.com';
$log  = __DIR__ . '/rfq-log.csv';   // keeps a copy of every request; delete this line to disable

header('Content-Type: application/json; charset=utf-8');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['ok'=>false,'error'=>'method']); exit; }
if (!empty($_POST['website'])) { echo json_encode(['ok'=>true,'ref'=>'ATC-RFQ-0000']); exit; } // honeypot filled by bots

$f = function($k, $max = 500) { $v = isset($_POST[$k]) ? trim((string)$_POST[$k]) : ''; return mb_substr(strip_tags($v), 0, $max); };
$name=$f('name'); $company=$f('company'); $email=$f('email'); $phone=$f('phone'); $code=$f('code'); $qty=$f('qty'); $unit=$f('unit',10);
$drum=$f('drum'); $city=$f('city'); $tender=$f('tender'); $notes=$f('notes',3000); $lang=$f('lang',5);
if ($name==='' || $code==='' || !filter_var($email, FILTER_VALIDATE_EMAIL)) { http_response_code(422); echo json_encode(['ok'=>false,'error'=>'fields']); exit; }

$ref = 'ATC-RFQ-' . date('Ymd') . '-' . strtoupper(substr(bin2hex(random_bytes(2)), 0, 4));
$lines = ["Reference: $ref", "Received: " . date('Y-m-d H:i'), "Language: $lang", "", "Name: $name", "Company: $company", "Email: $email", "Phone: $phone", "",
  "Conductor: $code", "Quantity: $qty $unit", "Length per drum: $drum m", "Delivery: $city", "Tender/project: $tender", "", "Notes:", $notes];
$body = implode("\n", $lines);
$headers = "From: Altawakol Cables website <$from>\r\nReply-To: $name <$email>\r\nContent-Type: text/plain; charset=UTF-8\r\n";
$sent = @mail($to, "RFQ $ref: $code ($company)", $body, $headers);
// confirmation to the requester
@mail($email, "Altawakol Cables: request $ref received", "Thank you. We have received your request for $code and will reply within one working day.\nReference: $ref\n\nAltawakol for Cables · Hotline 19796", "From: Altawakol Cables <$from>\r\nContent-Type: text/plain; charset=UTF-8\r\n");
if (!empty($log)) { $fp=@fopen($log,'a'); if($fp){ fputcsv($fp,[$ref,date('c'),$name,$company,$email,$phone,$code,$qty,$unit,$drum,$city,$tender,$notes]); fclose($fp);} }
echo json_encode(['ok'=>true, 'ref'=>$ref, 'mailed'=>(bool)$sent]); // logged even if mail() is not configured yet
