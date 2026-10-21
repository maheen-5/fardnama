import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../widgets/upload_widget.dart';

class EvidenceUploadScreen extends StatefulWidget {
  const EvidenceUploadScreen({
    super.key,
    required this.apiService,
    this.pickEvidence,
  });

  final ApiService apiService;
  final PickEvidence? pickEvidence;

  @override
  State<EvidenceUploadScreen> createState() => _EvidenceUploadScreenState();
}

class _EvidenceUploadScreenState extends State<EvidenceUploadScreen> {
  UploadResult? _result;
  String? _error;
  bool _isUploading = false;

  Future<void> _upload(List<int> bytes, String filename, bool consent) async {
    setState(() {
      _isUploading = true;
      _result = null;
      _error = null;
    });

    try {
      final result =
          await widget.apiService.uploadEvidence(bytes, filename, consent);
      if (mounted) {
        setState(() => _result = result);
      }
    } on ApiException catch (exception) {
      if (mounted) {
        setState(() => _error = exception.detail);
      }
    } catch (exception) {
      if (mounted) {
        setState(() => _error = 'Unable to upload evidence: $exception');
      }
    } finally {
      if (mounted) {
        setState(() => _isUploading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('FardNama Evidence Upload')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const Text(
              'Upload evidence',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            UploadWidget(
              onUpload: _upload,
              isUploading: _isUploading,
              pickEvidence: widget.pickEvidence,
            ),
            if (_isUploading) ...[
              const SizedBox(height: 24),
              const Center(child: CircularProgressIndicator()),
            ],
            if (_error case final error?) ...[
              const SizedBox(height: 24),
              Card(
                color: Theme.of(context).colorScheme.errorContainer,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(error),
                ),
              ),
            ],
            if (_result case final result?) ...[
              const SizedBox(height: 24),
              _ResultCard(result: result),
            ],
          ],
        ),
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});

  final UploadResult result;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Upload complete',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            const Text('SHA-256'),
            SelectableText(result.sha256),
            const SizedBox(height: 12),
            Text('OCR status: ${result.ocrStatus}'),
            if (result.extractedText != null &&
                result.extractedText!.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('Extracted text'),
              SelectableText(result.extractedText!),
            ],
          ],
        ),
      ),
    );
  }
}
