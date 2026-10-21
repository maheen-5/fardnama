import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

class PickedEvidence {
  const PickedEvidence({required this.bytes, required this.filename});

  final List<int> bytes;
  final String filename;
}

typedef PickEvidence = Future<PickedEvidence?> Function();
typedef UploadEvidence =
    Future<void> Function(List<int> bytes, String filename, bool consent);

class UploadWidget extends StatefulWidget {
  const UploadWidget({
    super.key,
    required this.onUpload,
    required this.isUploading,
    this.pickEvidence,
  });

  final UploadEvidence onUpload;
  final bool isUploading;
  final PickEvidence? pickEvidence;

  @override
  State<UploadWidget> createState() => _UploadWidgetState();
}

class _UploadWidgetState extends State<UploadWidget> {
  PickedEvidence? _selectedEvidence;
  bool _consent = false;
  bool _isPicking = false;

  bool get _canUpload =>
      _selectedEvidence != null && _consent && !widget.isUploading;

  Future<void> _pickFile() async {
    setState(() => _isPicking = true);
    try {
      final selected = await (widget.pickEvidence ?? _pickEvidence)();
      if (mounted && selected != null) {
        setState(() => _selectedEvidence = selected);
      }
    } finally {
      if (mounted) {
        setState(() => _isPicking = false);
      }
    }
  }

  Future<PickedEvidence?> _pickEvidence() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      withData: true,
      allowMultiple: false,
    );
    final file = result == null || result.files.isEmpty
        ? null
        : result.files.first;
    final bytes = file?.bytes;
    if (file == null || bytes == null) {
      return null;
    }
    return PickedEvidence(bytes: bytes, filename: file.name);
  }

  Future<void> _upload() async {
    final selected = _selectedEvidence;
    if (selected == null || !_consent || widget.isUploading) {
      return;
    }
    try {
      await widget.onUpload(selected.bytes, selected.filename, _consent);
    } finally {
      if (mounted) {
        setState(() => _selectedEvidence = null);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        OutlinedButton.icon(
          onPressed: _isPicking || widget.isUploading ? null : _pickFile,
          icon: const Icon(Icons.attach_file),
          label: const Text('Choose evidence file'),
        ),
        if (_selectedEvidence case final selected?) ...[
          const SizedBox(height: 8),
          Text('Selected: ${selected.filename}'),
        ],
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
          title: const Text('I consent to processing this evidence.'),
          value: _consent,
          onChanged: widget.isUploading
              ? null
              : (value) => setState(() => _consent = value ?? false),
        ),
        const SizedBox(height: 8),
        FilledButton(
          onPressed: _canUpload ? _upload : null,
          child: const Text('Upload'),
        ),
      ],
    );
  }
}
