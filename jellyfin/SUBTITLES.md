# Subtitles

A video's subtitles come from one of three places, and Jellyfin lists each in the player with nothing to set up:

- **The tracks the video file already carries**, such as the subtitle tracks of an `.mkv`. They are in sync with the video.
- **Bazarr** (`../bazarr/README.md`), which downloads from OpenSubtitles.com the Portuguese (Brazil) subtitle a video lacks and saves it next to the video with the same name and a language suffix. It needs the OpenSubtitles.com login (`TIDE_OPENSUBTITLES_USERNAME` and `TIDE_OPENSUBTITLES_PASSWORD` in `tide/.env`); without it Bazarr downloads none.
- **An `.srt` saved by hand** next to the video, named `Title (Year).pt-BR.srt`, when neither of the others has one.

A subtitle that comes in the download as an `.srt` is imported by Radarr and Sonarr next to the video, named like it (Import Extra Files).

Jellyfin downloads no subtitles: no subtitle plugin is installed. The Open Subtitles plugin was tried and removed, because it cannot ask for Brazilian Portuguese. Jellyfin stores a language as its ISO 639-2 code, where Portuguese (Brazil) and Portuguese (Portugal) are both `por`, and the plugin (v25) sends `por` to OpenSubtitles as `pt-PT`, so its downloads would be European Portuguese. Bazarr asks for Portuguese (Brazil) by its own code, `pb`, so the problem does not apply to it.

For the same reason, a Portuguese (Brazil) track shows the flag of Portugal in the language tags of Jellyfin Enhanced, which maps `por` to that flag; the name of the track still says Portuguese (Brazil).
