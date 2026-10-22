import 'package:flutter/material.dart';

import 'screens/case_companion_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const FardNamaApp());
}

class FardNamaApp extends StatelessWidget {
  const FardNamaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FardNama - Evidence Companion',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.theme,
      home: const CaseCompanionScreen(),
    );
  }
}
