
# colorFabb Filament Installer

Deze installer helpt je om de **officiële colorFabb printer/slicer profielen** te downloaden en te installeren op je Windows PC.

## Wat doet deze installer?

- Downloadt de nieuwste profielen (ZIP) vanaf GitHub.
- Controleert of de download/ZIP geldig is.
- Installeert de juiste profielbestanden in de juiste map(pen) voor ondersteunde slicers.

## Gebruik (voor gebruikers)

1. Download de nieuwste `colorFabbInstaller_vX.Y.Z.exe` uit **GitHub Releases**.
2. Dubbelklik om te starten.
3. Volg de stappen in het venster (selecteer slicer(s) / locatie(s) als daarom gevraagd wordt).
4. Klik **Install** en wacht tot “Done/Completed”.

Tip: als Windows waarschuwt (SmartScreen), controleer dan de **SHA256** (en digitale handtekening als signing is ingeschakeld) bij de release.

## Troubleshooting

- Downloadproblemen? Start de installer opnieuw en probeer opnieuw. Internet/SSL blokkades (proxy/AV) kunnen downloads verhinderen.
- Wil je alleen testen of downloaden/uitpakken werkt (zonder GUI install)?

```powershell
colorFabbInstaller_vX.Y.Z.exe --check-download
```

## Voor developers

Build/release instructies staan in `build.md`.
