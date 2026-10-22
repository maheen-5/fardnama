import 'package:flutter/material.dart';

abstract final class AppTheme {
  static const bark = Color(0xFF2A2E1F);
  static const leather = Color(0xFF586B3D);
  static const chestnut = Color(0xFF8E9A63);
  static const dunes = Color(0xFFEDE7D2);
  static const olive = Color(0xFF6E7B4B);
  static const oliveDeep = Color(0xFF4A5333);
  static const oliveSoft = Color(0xFFAEB48C);
  static const paper = Color(0xFFFFFFFF);
  static const paper2 = Color(0xFFF6F3E7);
  static const beige = Color(0xFFF1EBD9);
  static const sage = Color(0xFFE1E8D3);
  static const sage2 = Color(0xFFEFF3E5);
  static const line = Color(0xFFE1D9BD);
  static const brick = Color(0xFF7A3B2E);
  static const inkSoft = Color(0xFF6E7057);

  static ThemeData get theme => ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: beige,
        colorScheme: ColorScheme.fromSeed(
          seedColor: leather,
          primary: leather,
          surface: paper,
          error: brick,
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(color: bark, height: 1.55),
          bodyMedium: TextStyle(color: bark, height: 1.5),
          bodySmall: TextStyle(color: inkSoft, height: 1.5),
          titleLarge: TextStyle(
            color: bark,
            fontSize: 30,
            fontWeight: FontWeight.w600,
          ),
          titleMedium: TextStyle(
            color: bark,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: leather,
            foregroundColor: const Color(0xFFFBF3DD),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(9),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: oliveDeep,
            side: const BorderSide(color: line),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(9),
            ),
          ),
        ),
      );
}
