# Tervezett SFTP-kommunikáció

```mermaid
flowchart TD
    subgraph AGENT["1. Agent gépe"]
        START["Mentés indítása"] --> RESULT{"Sikerült a mentés?"}
        RESULT -->|Igen| PACK["Archívum + SHA-256<br/>+ JSON-eredményfájl"]
        RESULT -->|Nem| ERROR["JSON-hibajelentés"]
        PACK --> ID["Állandó csomagazonosító"]
        ERROR --> ID
        ID --> CONNECT["SFTP-kapcsolat<br/>SSH-kulcs + szerverkulcs ellenőrzése"]
        KEEP["Helyi csomag megőrzése<br/>a visszaigazolásig"]
        RETRY["Várakozás és újrapróbálás<br/>ugyanazzal az azonosítóval"]
        CONNECT -->|Kapcsolati hiba| RETRY
        RETRY --> CONNECT
    end

    subgraph SERVER["2. Fogadó szerver"]
        TEMP["Feltöltés ideiglenes könyvtárba"]
        READY["Minden fájl és a jegyzék megérkezett<br/>Átnevezés kész csomaggá"]
        CHECK["Feldolgozóprogram<br/>Csomagazonosító, JSON és fájlok vizsgálata"]
        TYPE{"Helyi mentés eredménye"}
        VERIFY["Méret és SHA-256 ellenőrzése"]
        RECORD["Helyi mentési hiba rögzítése"]
        SAVED["Átvételi eredmény tárolása<br/>Siker vagy hiba"]
        ACK["Visszaigazolás létrehozása"]
        MAIL["E-mail küldése az eredményről"]
        MAILRETRY["E-mailküldés újrapróbálása"]

        TEMP --> READY --> CHECK --> TYPE
        TYPE -->|Sikeres| VERIFY --> SAVED
        TYPE -->|Hibás| RECORD --> SAVED
        CHECK -->|Hiányos vagy hibás csomag| SAVED
        SAVED --> ACK
        SAVED --> MAIL
        MAIL -->|Küldési hiba| MAILRETRY --> MAIL
    end

    CONNECT -->|Feltöltés| TEMP
    TEMP -->|Megszakadt átvitel| RETRY
    ID --> KEEP
    ACK -->|Agent lekérdezi| CONFIRMED["3. Agent rögzíti a visszaigazolást"]
    KEEP -.-> CONFIRMED

    classDef failure fill:#fff0ee,stroke:#c64035,color:#76231c
    classDef success fill:#e9f7ee,stroke:#27834a,color:#174b2b
    classDef transfer fill:#edf4ff,stroke:#3979bf,color:#1c426b
    class ERROR,RECORD,RETRY,MAILRETRY failure
    class PACK,READY,CONFIRMED success
    class CONNECT,TEMP,ACK transfer
```

A JSON-hibajelentés ugyanazon az átadási útvonalon halad, mint a sikeres mentés csomagja. A szerver a teljesen feltöltött csomagot dolgozza fel, és a saját ellenőrzésének eredménye alapján küld értesítést.

Az ábra a tervezett működést mutatja. A helyi csomagok későbbi törlésének feltételeit külön határozzuk meg.
