# Betrieb

Wie man den Automaten startet, prüft und am Laufen hält. Stand: 9. September 2026.

## Was auf dem Pi läuft

Zwei Prozesse, die nichts voneinander wissen. **Teleop** liest den Leader-Arm und
schreibt die Gelenkwinkel auf den Follower, 60 Hz, als systemd-Dienst im Dauerlauf.
**Das Spiel** liest die Top-Down-Kamera, erkennt ArUco-Marker und rendert. Es fragt
den Armzustand nie ab.

Die beiden benutzen getrennte Python-Umgebungen und fassen sich nicht an:

| | Umgebung | Version |
|---|---|---|
| Teleop | conda, `~/miniforge3/envs/lerobot` | Python 3.10, LeRobot 0.4.2 |
| Spiel | uv, Projekt-`.venv` | Python 3.13, pygame-ce, OpenCV |

Hardware: Raspberry Pi 5 (8 GB) mit Ubuntu 24.04, zwei SO-101-Arme über CH343-Adapter,
zwei USB-Kameras, Display an HDMI-A-1.

> Das Spiel ist seit dem 9.9.2026 auf dem Pi installiert und startet. Es ist
> aber **nicht abgenommen**: es erreicht die Zielbildrate nicht und treibt den
> Pi zusammen mit der Teleop ins Drosseln. Siehe „Stand der Abnahme".

## Reinkommen

```sh
ssh picknplay
```

Der Eintrag steht in `~/.ssh/config` und zeigt auf `ubuntu@172.22.1.2`. Der Pi hängt
per WLAN am Makerspace-Netz, `eth0` ist tot. Die IP kommt per DHCP, kann sich also
ändern. Wenn nichts geht: pingen. Antwortet er auf Ping, aber Port 22 ist zu, läuft
`sshd` nicht, und du musst an die Tastatur am Gerät.

## Teleop starten und stoppen

```sh
sudo systemctl start teleop.service
sudo systemctl stop  teleop.service
sudo systemctl restart teleop.service
```

Der Dienst ist `enabled`, startet also beim Booten von allein.

## Läuft es?

```sh
systemctl is-active teleop.service
systemctl show teleop.service -p NRestarts -p SubState
vcgencmd measure_temp
vcgencmd get_throttled
```

Gesund sieht so aus: `active`, `SubState=running`, **`NRestarts=0`**, um die 55 bis 65 °C,
`throttled=0x0`.

`NRestarts` ist die wichtigste Zahl. Steigt sie, crasht der Dienst und startet neu, und
das ist immer ein Hardwareproblem: ein Arm ohne Strom, ein Kabel ab, ein Adapter nicht
erkannt. Softwarefehler sehen anders aus.

Im Normalbetrieb schreibt Teleop **nichts** ins Journal. Das ist Absicht (siehe „Warum
das Journal still ist"). Stille heißt: es läuft. Fehler landen weiterhin im Log:

```sh
journalctl -u teleop.service -b --no-pager | tail -30
```

### `get_throttled` lesen

Die Zahl ist eine Bitmaske. Wichtig sind vier Bits:

| Wert | Bedeutung |
|---|---|
| `0x0` | alles in Ordnung |
| `0x1` | Unterspannung **jetzt**, also Netzteil oder Kabel |
| `0x8` | Temperaturlimit **jetzt**, er drosselt gerade |
| `0x80000` | Temperaturlimit ist seit dem Boot mal aufgetreten |

`0x80008` heißt entsprechend: drosselt gerade und hat es schon vorher getan. Ab etwa
80 °C fängt das an.

## Motoren prüfen

Wenn Teleop crasht, ist die erste Frage: antworten überhaupt Servos? Das beantwortet
`tools/scan_motors.py`. Teleop muss dafür stehen, sonst sind die Ports belegt.

```sh
sudo systemctl stop teleop.service
~/miniforge3/envs/lerobot/bin/python ~/scan_motors.py
sudo systemctl start teleop.service
```

Das Skript liegt im Repo unter `tools/scan_motors.py` und als Kopie direkt in `~` auf dem
Pi, damit es auch ohne ausgechecktes Repo zur Hand ist.

Gesund:

```
/dev/ttyACM0 -> 1(m777), 2(m777), 3(m777), 4(m777), 5(m777), 6(m777)
/dev/ttyACM1 -> 1(m777), 2(m777), 3(m777), 4(m777), 5(m777), 6(m777)
```

Sechs Motoren pro Arm, IDs 1 bis 6, Modell 777 (STS3215). Alles andere ist ein Befund:

Ein Port meldet **keine Motoren**, obwohl er im Scan auftaucht. Dann fehlt die
Servo-Stromversorgung oder das dreiadrige Buskabel steckt nicht. Der USB-Adapter zieht
seinen Strom aus dem Pi und meldet sich auch ohne Servo-Netzteil, der Bus bleibt aber
still. Leader läuft auf 7,4 V, Follower auf 12 V.

Es fehlen **einzelne** Motoren mitten in der Kette, etwa 2 und 4, während 3, 5 und 6
antworten. Dann sind es nicht die Verbindungskabel, sondern die Servos selbst: Stecker
lose oder ID verstellt.

Ein Port **taucht gar nicht auf**. Dann ist ein USB-Adapter ab, und das ist der
gefährliche Fall, siehe nächster Abschnitt.

### Der Fall, der wie ein Servodefekt aussieht und keiner ist

Am 9.9.2026 fielen über Stunden Motoren aus, und zwar wechselnd: erst 2 und 4,
dann alle sechs, dann 4 und 6. Der Scan fand jedes Mal alle sechs, LeRobot
scheiterte trotzdem. Die Ursache war das **Netzteil, das auf 5 V stand**.

Der Grund, warum das so schwer zu sehen ist: ein Ping zieht fast keinen Strom,
deshalb antworten bei Unterspannung alle Motoren brav im Scan. Sobald LeRobot
aber Torque aktiviert, brechen die zwei ein, die am meisten ziehen — bei einem
SO-101 sind das 4 (Wrist-Flex) und 6 (Greifer), weil die gegen die Schwerkraft
arbeiten. Sie fallen vom Bus, und die Fehlermeldung sagt „Missing motor IDs".

**Merkregel: wechselnde Motor-IDs bedeuten Spannung, feste bedeuten Hardware.**
Fällt immer derselbe Motor aus, ist es der Motor oder sein Stecker. Wechselt es,
miss zuerst die Spannung. Follower 12 V, Leader 7,4 V.

### Der erste Startversuch scheitert manchmal

Auch bei korrekter Spannung schlägt der erste Verbindungsversuch gelegentlich
fehl und der zweite läuft. Deshalb steht `Restart=on-failure` im Override, und
deshalb ist `NRestarts=1` nach einem Start kein Grund zur Sorge. Erst eine
steigende Zahl ist einer.

## Welcher Adapter ist welcher Arm

```sh
ls -l /dev/serial/by-id/
```

```
usb-1a86_USB_Single_Serial_5970072402-if00 -> ttyACM0    Leader
usb-1a86_USB_Single_Serial_5970073917-if00 -> ttyACM1    Follower
```

`run_teleop.sh` übergibt `ttyACM0` als Leader und `ttyACM1` als Follower. Diese Nummern
vergibt der Kernel in der Reihenfolge, in der die Geräte auftauchen. Steckt ein Adapter
nicht, rutschen alle dahinter eine Nummer hoch: aus `ttyACM1` wird `ttyACM0`, und Teleop
redet mit dem Follower, als wäre er der Leader.

Genau das ist am 9. September passiert. Der Fehler meldet sich als „Missing motor IDs"
und sieht nach kaputten Servos aus, obwohl nur ein Kabel fehlte. Erste Handlung bei
diesem Fehler ist deshalb immer `ls -l /dev/serial/by-id/`, nicht der Motor-Scan.

Die Seriennummern sind fest und rutschen nie. Der saubere Umbau ist, sie in
`run_teleop.sh` einzutragen statt der `ttyACM*`-Nummern. Steht noch aus.

## Wartung

Einmal im Monat oder wenn etwas komisch ist:

```sh
df -h /                    # unter 85 % halten
journalctl --disk-usage    # gedeckelt auf 200 MB
vcgencmd measure_temp
systemctl show teleop.service -p NRestarts
```

Wenn die Platte doch volläuft, in dieser Reihenfolge:

```sh
sudo journalctl --rotate && sudo journalctl --vacuum-size=200M
sudo rm -f /var/log/syslog.1 /var/log/syslog.*.gz
rm -rf ~/.cache/pip ~/.cache/huggingface/hub ~/.cache/huggingface/xet
rm -rf ~/.vscode-server
```

**Nicht** `~/.cache` komplett löschen. Da drin liegt die Armkalibrierung:

```
~/.cache/huggingface/lerobot/calibration/robots/so101_follower/my_follower_arm.json
~/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/my_leader_arm.json
```

Zwei Dateien, zusammen keine 2 KB, vom 31. März. Sind sie weg, muss neu kalibriert
werden. Ein Backup davon auf dem MacBook wäre klug.

### Warum das Journal still ist

Teleop druckte pro Loop-Durchlauf eine Zeile Loop-Zeit, bei 60 Hz also 60 Zeilen pro
Sekunde. Das waren 99,7 % des gesamten Journals und rund 1 GB pro Tag, weil journald und
rsyslog denselben Strom doppelt wegschrieben. Journalds eingebautes Ratelimit greift bei
60 Zeilen pro Sekunde nicht, das liegt unter der Schwelle.

Zwei Änderungen halten das jetzt in Schach. `SystemMaxUse=200M` in
`/etc/systemd/journald.conf` deckelt das Journal. Und in
`/etc/systemd/system/teleop.service.d/override.conf`:

```ini
[Unit]
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Restart=on-failure
StandardOutput=null
```

`StandardOutput=null` schluckt den Debug-Print. Die beiden `StartLimit`-Zeilen sind der
Hitzeschutz: bei einem Hardwarefehler hielt der Dienst vorher mit `Restart=always` nie an
und startete sich in 30 Minuten 153-mal neu, jedes Mal mit dem vollen Laden von torch.
Der Pi kam auf 82 °C und drosselte. Jetzt bleibt er nach fünf Fehlversuchen in zwei
Minuten stehen und meldet das, statt zu heizen.

## Wenn etwas nicht geht

| Symptom | Erste Prüfung | Meist die Ursache |
|---|---|---|
| `ssh` sagt Connection refused, Ping geht | an die Tastatur am Gerät, `df -h /` | Platte voll, `sshd` startet nicht |
| `ssh` sagt Timeout | `arp -n 172.22.1.2` | Pi aus, oder neue IP per DHCP |
| `NRestarts` steigt | `journalctl -u teleop.service -b \| tail -30` | Hardware, nie Software |
| „Missing motor IDs" | `ls -l /dev/serial/by-id/` | Adapter ab, Nummern verrutscht |
| Ein Bus schweigt komplett | Servo-Netzteil und Buskabel | Strom fehlt, nicht die Servos |
| Einzelne Motoren fehlen sprunghaft, mal 2 und 4, mal 4 und 6 | **Spannung am Netzteil messen** | Unterspannung. Siehe unten |
| Über 80 °C | `systemctl show teleop.service -p NRestarts` | Crash-Loop heizt den Pi |
| Platte über 85 % | `journalctl --disk-usage` | siehe „Wartung" |

## Das Spiel starten

```sh
cd ~/picknplay
.venv/bin/python game/main.py
```

Läuft über KMSDRM im Vollbild, ohne Desktop. **Achtung:** über SSH gibt es dabei
keine Tastatureingabe, SDL liest bei KMSDRM aus `/dev/input`. Zum Bedienen
gehört eine USB-Tastatur an den Pi, zum Beenden `q`.

Startest du es aus einer SSH-Sitzung, hänge immer ein `timeout` davor. Sonst
läuft es weiter, wenn die Sitzung abbricht, und ein ausgelasteter Pi lässt keine
neue Anmeldung mehr zu:

```sh
timeout -s KILL 30 .venv/bin/python game/main.py
```

### Schalter zum Messen und Entwickeln

Alle per Umgebungsvariable, Default ist immer der Automat. Die Datei muss man
dafür nicht anfassen, was wichtig ist, weil das nächste `git pull` lokale
Änderungen einkassiert.

| Variable | Wirkung |
|---|---|
| `PNP_FULLSCREEN=0` | Fenster statt Vollbild |
| `PNP_CAMERA=0` | `FakeDetector`, kein Kamerazugriff |
| `PNP_FPSLOG=1` | Bildrate und Szene, einmal pro Sekunde auf stdout |
| `PNP_CRT=0` | CRT-Overlay komplett aus |
| `PNP_BARREL=0` | nur die Wölbung aus, Scanlines bleiben |
| `PNP_IDLE_FPS=60` | Idle-Screen auf Spielszenen-Last, für Messungen ohne Tastatur |

## Stand der Abnahme

Installiert und geprüft: `uv`, Python 3.13, OpenCV 5.0, pygame-ce 2.5.8, alle
vier Selbsttests grün, beide Kameras liefern Bild, KMSDRM startet, Ton über
HDMI vorhanden.

Nicht abgenommen: **die Bildrate.** Ziel sind 60 fps, gemessen wurden 19,6 mit
vollem CRT und 40 im entkernten Zustand. Mit Spiel und Teleop gleichzeitig geht
der Pi in unter einer Minute auf 83 °C und drosselt. Die Zahlen und die drei
Stellschrauben stehen im Overview unter „Messung auf dem Pi".

**Bis das entschieden ist, nicht beides gleichzeitig dauerhaft laufen lassen.**

## Offen

1. Entscheidung zur Bildrate: Wölbung streichen, auf 1920 × 1080 nativ umziehen,
   oder Zielbildrate auf 30 senken. Entwurfsfrage, keine Konfigurationsfrage.
2. Aktive Kühlung. Ohne Lüfter drosselt der Pi unter Doppellast.
3. Layout auf 1080, falls Punkt 1 so ausgeht. `FOOTER_Y = 1120` liegt sonst
   außerhalb des Bildes.
4. Ton am Automatenlautsprecher abhören. Es gibt nur HDMI-Audio, keine USB-Karte.
   Beim Testlauf traten ALSA-Underruns auf.
5. ArUco-Erkennungsrate gegen die gedruckten Marker. Beim Testlauf lagen keine
   auf dem Tablett.
6. `picknplay.service` schreiben, mit `After=teleop.service`, aber ohne
   `Requires` — das Spiel soll auch ohne Arme starten.
7. Die Arm-Kamera hängt um 90° verdreht. Der Passthrough steht damit quer.

Dazu die zwei Stabilitätsumbauten: Seriennummern statt `ttyACM*` in
`run_teleop.sh`, und Kameras über `/dev/v4l/by-path/` statt über Indizes. Beide
Kameras melden denselben USB-Serial, `by-id` unterscheidet sie also nicht, nur
der physische Port tut das.
