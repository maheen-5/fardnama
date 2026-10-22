# FardNama Flutter demonstration

This Flutter client recreates the screens and interaction flow in
[`../docs/ui-prototype/index_1.html`](../docs/ui-prototype/index_1.html).
It starts with a consent notice and mocked login, then presents all nine
prototype steps. The screens use example data and do not connect to a backend.
Selecting files only displays their names locally; it does not upload or store
them.

The processing screen includes the supplied Error Level Analysis (ELA) report
as fixed demonstration data. ELA highlights are explicitly described as
indications to review, not proof of image editing. SOS also only simulates an
alert and example nearby places; it does not access location or message anyone.

## Run the app

Install Flutter and its platform prerequisites, then in PowerShell:

```powershell
cd frontend
flutter pub get
flutter run
```

To run in Chrome, list available targets with `flutter devices`, then run
`flutter run -d chrome`. For an Android emulator, start an emulator first and
run `flutter run` (or specify the device ID shown by `flutter devices`).

Run the Flutter tests from this directory with:

```powershell
flutter test
```

## Source structure

- `lib/main.dart` — Flutter entry point. Creates the `MaterialApp`, applies the
  shared theme, and opens the demonstration flow.
- `lib/screens/case_companion_screen.dart` — Consent and login gates, language
  switching, responsive navigation, all nine screen contents, file selection,
  report-preview and chat interactions, and the simulated SOS dialog.
- `lib/l10n/app_copy.dart` — English and Urdu interface copy and display text.
- `lib/models/demo_case.dart` — Step metadata and fixture values, including the
  ELA measurements copied from `backend/forensics_results/ela_report.json`.
- `lib/theme/app_theme.dart` — Shared palette and Material theme matching the
  prototype's beige, sage, olive, and dark-green design.
- `lib/screens/evidence_upload_screen.dart` — The earlier standalone backend
  upload screen. It remains available for later API integration but is not the
  current app entry screen.
- `lib/widgets/upload_widget.dart` — Reusable file picker and consent widget
  used by the standalone upload screen.
- `lib/services/api_service.dart` — Multipart upload client and response
  parsing for the backend evidence endpoint; not used by the demo flow.
- `test/case_companion_screen_test.dart` — Widget tests for consent/login
  progression and ELA report rendering.
- `test/upload_screen_test.dart` — Existing tests for the standalone API upload
  screen and result rendering.
- `pubspec.yaml` — Flutter package metadata, dependencies, and assets setup.
- `analysis_options.yaml` — Dart/Flutter lint configuration.
