import 'package:flutter/material.dart';

import 'screens/evidence_upload_screen.dart';
import 'services/api_service.dart';

void main() {
  const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
  runApp(FardNamaApp(apiService: ApiService(baseUrl: baseUrl)));
}

class FardNamaApp extends StatelessWidget {
  const FardNamaApp({super.key, required this.apiService});

  final ApiService apiService;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FardNama',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF345C50)),
        useMaterial3: true,
      ),
      home: EvidenceUploadScreen(apiService: apiService),
    );
  }
}
