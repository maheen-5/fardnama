import 'package:fardnama_app/screens/case_companion_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('consent and login open the nine-step demonstration', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(home: CaseCompanionScreen()),
    );

    expect(find.text('Before you continue'), findsOneWidget);
    final continueButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Continue'),
    );
    expect(continueButton.onPressed, isNull);

    await tapVisible(tester, find.byType(Checkbox));
    final acceptedContinueButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Continue'),
    );
    expect(acceptedContinueButton.onPressed, isNotNull);
    await tapVisible(
      tester,
      find.widgetWithText(FilledButton, 'Continue'),
    );

    expect(find.text('Welcome back'), findsOneWidget);
    await tapVisible(tester, find.widgetWithText(FilledButton, 'Log in'));

    expect(find.text('Step 1 of 9'), findsOneWidget);
    expect(find.text('Add your evidence'), findsOneWidget);
  });

  testWidgets('processing step shows the supplied ELA report values', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(home: CaseCompanionScreen()),
    );

    await tapVisible(tester, find.byType(Checkbox));
    await tapVisible(
      tester,
      find.widgetWithText(FilledButton, 'Continue'),
    );
    await tapVisible(tester, find.widgetWithText(FilledButton, 'Log in'));
    await tapVisible(tester, find.textContaining('Continue to'));

    expect(find.text('ELA image integrity check'), findsOneWidget);
    expect(find.text('jpeg_original.jpg'), findsOneWidget);
    expect(find.text('jpeg_edited.jpg'), findsWidgets);
    expect(find.textContaining('4.08×'), findsWidgets);
    expect(find.textContaining('not proof of editing'), findsOneWidget);
  });
}
