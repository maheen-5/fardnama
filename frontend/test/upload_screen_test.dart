import 'package:fardnama_app/screens/evidence_upload_screen.dart';
import 'package:fardnama_app/services/api_service.dart';
import 'package:fardnama_app/widgets/upload_widget.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeApiService extends ApiService {
  _FakeApiService()
      : super(baseUrl: 'http://localhost');

  @override
  Future<UploadResult> uploadEvidence(
    List<int> bytes,
    String filename,
    bool consent,
  ) async {
    return UploadResult(
      evidenceId: 'evidence-id',
      sha256: List.filled(64, 'a').join(),
      ocrStatus: 'completed',
      extractedText: 'Sample text',
    );
  }
}

void main() {
  testWidgets('Upload button is disabled without consent', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: EvidenceUploadScreen(
          apiService: _FakeApiService(),
          pickEvidence: () async =>
              const PickedEvidence(bytes: [1, 2, 3], filename: 'sample.txt'),
        ),
      ),
    );

    await tester.tap(find.text('Choose evidence file'));
    await tester.pumpAndSettle();

    final uploadButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Upload'),
    );
    expect(uploadButton.onPressed, isNull);
  });

  testWidgets('Upload result renders the SHA-256', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: EvidenceUploadScreen(
          apiService: _FakeApiService(),
          pickEvidence: () async =>
              const PickedEvidence(bytes: [1, 2, 3], filename: 'sample.txt'),
        ),
      ),
    );

    await tester.tap(find.text('Choose evidence file'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('I consent to processing this evidence.'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Upload'));
    await tester.pumpAndSettle();

    expect(find.text(List.filled(64, 'a').join()), findsOneWidget);
  });
}
