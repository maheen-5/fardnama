import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.statusCode, this.detail);

  final int statusCode;
  final String detail;

  @override
  String toString() => detail;
}

class UploadResult {
  const UploadResult({
    required this.evidenceId,
    required this.sha256,
    required this.ocrStatus,
    required this.extractedText,
  });

  final String evidenceId;
  final String sha256;
  final String ocrStatus;
  final String? extractedText;

  factory UploadResult.fromJson(Map<String, dynamic> json) {
    return UploadResult(
      evidenceId: json['evidence_id'] as String,
      sha256: json['sha256'] as String,
      ocrStatus: json['ocr_status'] as String,
      extractedText: json['extracted_text'] as String?,
    );
  }
}

class ApiService {
  ApiService({required this.baseUrl});

  final String baseUrl;

  Future<UploadResult> uploadEvidence(
    List<int> bytes,
    String filename,
    bool consent,
  ) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('${baseUrl.replaceFirst(RegExp(r'/+$'), '')}/api/evidence/upload'),
    )
      ..fields['consent'] = consent ? 'true' : 'false'
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: filename,
        ),
      );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode != 201) {
      throw ApiException(response.statusCode, _errorDetail(response));
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return UploadResult.fromJson(body);
  }

  String _errorDetail(http.Response response) {
    try {
      final body = jsonDecode(response.body);
      if (body is Map<String, dynamic> && body['detail'] is String) {
        return body['detail'] as String;
      }
    } on FormatException {
      // Non-JSON error bodies are surfaced as-is below.
    }
    return response.body.isEmpty
        ? 'Request failed with status ${response.statusCode}.'
        : response.body;
  }
}
