import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../l10n/app_copy.dart';
import '../models/demo_case.dart';
import '../theme/app_theme.dart';

class CaseCompanionScreen extends StatefulWidget {
  const CaseCompanionScreen({super.key});

  @override
  State<CaseCompanionScreen> createState() => _CaseCompanionScreenState();
}

class _CaseCompanionScreenState extends State<CaseCompanionScreen> {
  bool _isUrdu = false;
  bool _acceptedNotice = false;
  bool _useUsername = false;
  bool _isLoggedIn = false;
  bool _reportGenerated = false;
  int _activeStep = 0;
  final Set<String> _platforms = {};
  final Set<String> _expandedEvidence = {};
  final List<String> _selectedFiles = [];
  String? _chatReply;

  AppCopy get _copy => AppCopy(_isUrdu);
  String t(String key) => _copy.call(key);

  void _changeLanguage(bool isUrdu) {
    setState(() => _isUrdu = isUrdu);
  }

  void _continueFromNotice() {
    if (_acceptedNotice) {
      setState(() => _activeStep = -1);
    }
  }

  void _startDemo() {
    setState(() {
      _isLoggedIn = true;
      _activeStep = 0;
    });
  }

  void _goToStep(int index) {
    setState(() {
      _activeStep = index.clamp(0, 8).toInt();
      _chatReply = null;
    });
  }

  Future<void> _pickFiles() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: true,
      );
      if (!mounted || result == null) return;
      setState(() {
        _selectedFiles.addAll(
          result.files.map((file) => file.name).where(
                (name) => !_selectedFiles.contains(name),
              ),
        );
      });
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${t('chooseFiles')}: $error'),
          backgroundColor: AppTheme.brick,
        ),
      );
    }
  }

  void _showSosDialog() {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => _SosDialog(copy: _copy),
    );
  }

  Widget _languageSwitch({bool onDark = false}) {
    final background =
        onDark ? Colors.white.withOpacity(.08) : AppTheme.bark.withOpacity(.06);
    return Container(
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      padding: const EdgeInsets.all(3),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _LanguageChoice(
            label: 'EN',
            selected: !_isUrdu,
            onDark: onDark,
            onTap: () => _changeLanguage(false),
          ),
          _LanguageChoice(
            label: 'اردو',
            selected: _isUrdu,
            onDark: onDark,
            onTap: () => _changeLanguage(true),
          ),
        ],
      ),
    );
  }

  Widget _brand({bool onDark = false}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            gradient: RadialGradient(
              center: Alignment(-.35, -.4),
              colors: [Color(0xFF9AA873), AppTheme.leather],
            ),
          ),
          child: const Icon(
            Icons.shield_outlined,
            size: 18,
            color: Color(0xFFF6EFDD),
          ),
        ),
        const SizedBox(width: 10),
        Text(
          'FardNama',
          style: TextStyle(
            fontFamily: 'Georgia',
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: onDark ? const Color(0xFFF5F2DE) : AppTheme.bark,
          ),
        ),
      ],
    );
  }

  Widget _gateScreen({required Widget child}) {
    return Container(
      decoration: const BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(-.85, -.95),
          radius: 1.4,
          colors: [Color(0xFFE2E7D3), AppTheme.beige],
        ),
      ),
      child: SafeArea(
        child: Stack(
          children: [
            PositionedDirectional(
              top: 18,
              end: 22,
              child: _languageSwitch(),
            ),
            Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(18, 70, 18, 24),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 520),
                  child: child,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _gateCard({required List<Widget> children}) {
    return Container(
      padding: EdgeInsets.all(
        MediaQuery.of(context).size.width < 560 ? 22 : 36,
      ),
      decoration: BoxDecoration(
        color: AppTheme.paper,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.line),
        boxShadow: [
          BoxShadow(
            color: AppTheme.bark.withOpacity(.14),
            blurRadius: 42,
            offset: const Offset(0, 18),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    );
  }

  Widget _noticeScreen() {
    final items = [
      ('§', 'pecaAligned', 'pecaBody'),
      ('🔒', 'privateTitle', 'privateBody'),
      ('✋', 'noAutoTitle', 'noAutoBody'),
      ('🕊', 'deleteTitle', 'deleteBody'),
      ('🪪', 'caseIdTitle', 'caseIdBody'),
      ('☎', 'emergencyTitle', 'emergencyBody'),
    ];
    return _gateScreen(
      child: _gateCard(
        children: [
          _brand(),
          const SizedBox(height: 22),
          Text(t('beforeContinue'), style: _gateTitleStyle()),
          const SizedBox(height: 6),
          Text(t('readRights'), style: _gateSubtitleStyle()),
          const SizedBox(height: 14),
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 330),
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 14),
              itemBuilder: (context, index) {
                final item = items[index];
                return _NoticeItem(
                  iconText: item.$1,
                  title: t(item.$2),
                  body: t(item.$3),
                );
              },
            ),
          ),
          const SizedBox(height: 14),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            activeColor: AppTheme.olive,
            value: _acceptedNotice,
            onChanged: (value) =>
                setState(() => _acceptedNotice = value ?? false),
            title: Text(
              t('agreeNotice'),
              style: const TextStyle(color: AppTheme.inkSoft, fontSize: 12.5),
            ),
          ),
          const SizedBox(height: 4),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _acceptedNotice ? _continueFromNotice : null,
              child: Text(t('continue')),
            ),
          ),
          const SizedBox(height: 14),
          _demoNotice(),
        ],
      ),
    );
  }

  Widget _loginScreen() {
    return _gateScreen(
      child: _gateCard(
        children: [
          _brand(),
          const SizedBox(height: 22),
          Text(t('welcomeBack'), style: _gateTitleStyle()),
          const SizedBox(height: 6),
          Text(t('loginSub'), style: _gateSubtitleStyle()),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: AppTheme.paper2,
              borderRadius: BorderRadius.circular(11),
            ),
            child: Row(
              children: [
                _LoginTab(
                  label: t('caseNumber'),
                  selected: !_useUsername,
                  onTap: () => setState(() => _useUsername = false),
                ),
                _LoginTab(
                  label: t('username'),
                  selected: _useUsername,
                  onTap: () => setState(() => _useUsername = true),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          if (!_useUsername) ...[
            _fieldLabel(t('caseNumber'), t('assignedHint')),
            const SizedBox(height: 6),
            _loginField(initialValue: DemoCase.caseNumber),
          ] else ...[
            _fieldLabel(t('username')),
            const SizedBox(height: 6),
            _loginField(hint: t('usernameHint')),
          ],
          const SizedBox(height: 14),
          _fieldLabel(t('password'), _useUsername ? null : t('passwordHint')),
          const SizedBox(height: 6),
          _loginField(hint: '••••••••', obscure: true),
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _startDemo,
              child: Text(t('login')),
            ),
          ),
          const SizedBox(height: 14),
          Text(t('loginNote'), style: _smallNoteStyle()),
          const SizedBox(height: 12),
          _demoNotice(),
        ],
      ),
    );
  }

  Widget _loginField({
    String? initialValue,
    String? hint,
    bool obscure = false,
  }) {
    return TextFormField(
      initialValue: initialValue,
      obscureText: obscure,
      textDirection: initialValue != null ? TextDirection.ltr : null,
      decoration: InputDecoration(
        hintText: hint,
        filled: true,
        fillColor: AppTheme.paper2,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 13, vertical: 11),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppTheme.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppTheme.olive),
        ),
      ),
    );
  }

  Widget _fieldLabel(String label, [String? hint]) {
    return RichText(
      text: TextSpan(
        style: const TextStyle(
          color: AppTheme.bark,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
        children: [
          TextSpan(text: label),
          if (hint != null)
            TextSpan(
              text: '  $hint',
              style: const TextStyle(
                color: AppTheme.inkSoft,
                fontWeight: FontWeight.normal,
              ),
            ),
        ],
      ),
    );
  }

  TextStyle _gateTitleStyle() => const TextStyle(
        color: AppTheme.bark,
        fontFamily: 'Georgia',
        fontSize: 23,
        fontWeight: FontWeight.w600,
      );

  TextStyle _gateSubtitleStyle() => const TextStyle(
        color: AppTheme.inkSoft,
        fontSize: 13.5,
        height: 1.65,
      );

  TextStyle _smallNoteStyle() => const TextStyle(
        color: AppTheme.inkSoft,
        fontSize: 11.5,
        height: 1.55,
      );

  Widget _demoNotice() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: AppTheme.sage2,
        border: Border.all(color: const Color(0xFFD9E2C6)),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Text(
        '${t('demoMode')} · ${t('demoDisclaimer')}',
        style: const TextStyle(
          color: AppTheme.oliveDeep,
          fontSize: 11,
          height: 1.45,
        ),
      ),
    );
  }

  Widget _sidebar() {
    return Container(
      width: 280,
      height: double.infinity,
      padding: const EdgeInsets.fromLTRB(22, 24, 22, 20),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF3A4028), Color(0xFF262B19)],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [_brand(onDark: true), _languageSwitch(onDark: true)],
          ),
          Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(44, 9, 0, 20),
            child: Text(
              t('brandTagline'),
              style: const TextStyle(
                color: Color(0xFFAEB48F),
                fontSize: 12.5,
                height: 1.5,
              ),
            ),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: DemoCase.steps.length,
              itemBuilder: (context, index) => _sidebarStep(index),
            ),
          ),
          const Divider(color: Color(0x22FFFFFF)),
          Text(
            '${t('signedIn')}  ${DemoCase.caseNumber}\n${t('privacyNote')}',
            style: const TextStyle(
              color: Color(0xFF8D9271),
              fontSize: 11.5,
              height: 1.7,
            ),
          ),
        ],
      ),
    );
  }

  Widget _sidebarStep(int index) {
    final active = index == _activeStep;
    final done = index < _activeStep;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _goToStep(index),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 9),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 31,
                height: 31,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: active
                      ? AppTheme.chestnut
                      : done
                          ? AppTheme.oliveDeep
                          : const Color(0xFF2F3521),
                  border: Border.all(
                    color: active
                        ? const Color(0xFFC3CB9F)
                        : done
                            ? const Color(0xFF7C8657)
                            : const Color(0xFF5C6540),
                  ),
                ),
                child: Center(
                  child: Text(
                    done ? '✓' : '${index + 1}',
                    style: TextStyle(
                      color: active ? AppTheme.bark : const Color(0xFFE5E7CE),
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t('stepTitle$index'),
                        style: TextStyle(
                          color: active
                              ? const Color(0xFFFAF8E8)
                              : const Color(0xFFE7E5CC),
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        t('stepDesc$index'),
                        style: const TextStyle(
                          color: Color(0xFF8D9271),
                          fontSize: 11,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _mobileNavigation() {
    return Container(
      color: const Color(0xFF303621),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(child: _brand(onDark: true)),
              _languageSwitch(onDark: true),
            ],
          ),
          const SizedBox(height: 9),
          SizedBox(
            height: 59,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: DemoCase.steps.length,
              itemBuilder: (context, index) {
                final active = index == _activeStep;
                final done = index < _activeStep;
                return InkWell(
                  onTap: () => _goToStep(index),
                  child: SizedBox(
                    width: 73,
                    child: Column(
                      children: [
                        Container(
                          width: 27,
                          height: 27,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: active
                                ? AppTheme.chestnut
                                : done
                                    ? AppTheme.oliveDeep
                                    : const Color(0xFF2F3521),
                            border: Border.all(
                              color: active
                                  ? const Color(0xFFC3CB9F)
                                  : const Color(0xFF5C6540),
                            ),
                          ),
                          child: Center(
                            child: Text(
                              done ? '✓' : '${index + 1}',
                              style: const TextStyle(
                                color: Color(0xFFF5F2DE),
                                fontSize: 11,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          t('stepTitle$index'),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: active
                                ? const Color(0xFFFAF8E8)
                                : const Color(0xFFE7E5CC),
                            fontSize: 9.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _appScreen() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 780;
        final content = Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (compact) _mobileNavigation(),
            Expanded(
              child: Stack(
                children: [
                  SingleChildScrollView(
                    key: ValueKey('step-$_activeStep-$_isUrdu'),
                    padding: EdgeInsetsDirectional.fromSTEB(
                      compact ? 16 : 52,
                      compact ? 24 : 40,
                      compact ? 16 : 52,
                      92,
                    ),
                    child: Align(
                      alignment: AlignmentDirectional.topStart,
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 980),
                        child: _mainContent(),
                      ),
                    ),
                  ),
                  PositionedDirectional(
                    end: compact ? 14 : 26,
                    bottom: compact ? 14 : 26,
                    child: _sosButton(compact),
                  ),
                ],
              ),
            ),
          ],
        );

        return Row(
          children: [
            if (!compact) _sidebar(),
            Expanded(child: content),
          ],
        );
      },
    );
  }

  Widget _mainContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          t('stepOf').replaceAll('{n}', '${_activeStep + 1}'),
          style: const TextStyle(
            color: AppTheme.inkSoft,
            fontSize: 12.5,
            fontWeight: FontWeight.w600,
            letterSpacing: .3,
          ),
        ),
        const SizedBox(height: 11),
        Container(
          width: 38,
          height: 4,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            gradient: const LinearGradient(
              colors: [AppTheme.olive, AppTheme.chestnut],
            ),
          ),
        ),
        const SizedBox(height: 14),
        _buildStep(),
        const SizedBox(height: 30),
        const Divider(color: AppTheme.line),
        const SizedBox(height: 18),
        _stepNavigation(),
      ],
    );
  }

  Widget _pageHeading(String title, String description) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: _gateTitleStyle().copyWith(fontSize: 30)),
          const SizedBox(height: 7),
          Text(
            description,
            style: const TextStyle(
              color: AppTheme.inkSoft,
              fontSize: 14.5,
              height: 1.7,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep() {
    switch (_activeStep) {
      case 0:
        return _uploadStep();
      case 1:
        return _processingStep();
      case 2:
        return _classificationStep();
      case 3:
        return _assessmentStep();
      case 4:
        return _timelineStep();
      case 5:
        return _vaultStep();
      case 6:
        return _reportStep();
      case 7:
        return _supportStep();
      default:
        return _safetyStep();
    }
  }

  Widget _uploadStep() {
    final platformOptions = [
      ('whatsapp', 'whatsapp'),
      ('instagram', 'instagram'),
      ('messenger', 'messenger'),
      ('discord', 'discord'),
      ('snapchat', 'snapchat'),
      ('plainText', 'plainText'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('uploadTitle'), t('uploadDesc')),
        _DemoCard(
          child: Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.fromLTRB(18, 36, 18, 30),
                decoration: BoxDecoration(
                  color: AppTheme.sage2,
                  border: Border.all(
                    color: AppTheme.oliveSoft,
                    style: BorderStyle.solid,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  children: [
                    const Icon(
                      Icons.cloud_upload_outlined,
                      size: 44,
                      color: AppTheme.olive,
                    ),
                    const SizedBox(height: 13),
                    Text(
                      t('dropTitle'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppTheme.bark,
                        fontSize: 14.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      t('dropDesc'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppTheme.inkSoft,
                        fontSize: 12.5,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 15),
                    Wrap(
                      spacing: 7,
                      runSpacing: 7,
                      alignment: WrapAlignment.center,
                      children: [
                        for (final option in platformOptions)
                          FilterChip(
                            label: Text(t(option.$2)),
                            selected: _platforms.contains(option.$1),
                            onSelected: (selected) {
                              setState(() {
                                if (selected) {
                                  _platforms.add(option.$1);
                                } else {
                                  _platforms.remove(option.$1);
                                }
                              });
                            },
                            showCheckmark: false,
                            backgroundColor: AppTheme.sage,
                            selectedColor: AppTheme.olive,
                            labelStyle: TextStyle(
                              color: _platforms.contains(option.$1)
                                  ? Colors.white
                                  : AppTheme.oliveDeep,
                              fontSize: 11.5,
                            ),
                            side: const BorderSide(color: Color(0xFFCFDBB8)),
                          ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    OutlinedButton.icon(
                      onPressed: _pickFiles,
                      icon: const Icon(Icons.attach_file),
                      label: Text(t('chooseFiles')),
                    ),
                    if (_selectedFiles.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        t('filesSelected').replaceAll(
                          '{count}',
                          '${_selectedFiles.length}',
                        ),
                        style: const TextStyle(
                          color: AppTheme.oliveDeep,
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      for (final file in _selectedFiles)
                        Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(
                            file,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: AppTheme.inkSoft,
                              fontSize: 12,
                            ),
                          ),
                        ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _twoColumn(
          _DemoCard(
            title: t('captureTitle'),
            subtitle: t('captureSub'),
            child: _fieldList([
              ('timestamp', 'autoDetected'),
              ('deviceSource', 'autoDetected'),
              ('platform', 'autoDetected'),
              ('fileSize', 'autoDetected'),
            ]),
          ),
          _DemoCard(
            title: t('accountTitle'),
            subtitle: t('accountSub'),
            child: _fieldList([
              ('signIn', 'secureLogin'),
              ('caseCreated', 'Sep 2, 2026'),
              ('passwordReset', 'anytime'),
              ('access', 'onlyYou'),
            ]),
          ),
        ),
        const SizedBox(height: 18),
        _Disclaimer(text: t('controlNote')),
      ],
    );
  }

  Widget _processingStep() {
    final tasks = [
      (true, 'textExtracted', 'IMG_0231.png · WhatsApp'),
      (true, 'chatParsed', 'export.json · Instagram'),
      (true, 'fingerprintRecorded', 'fingerprintSub'),
      (false, 'readingDocument', 'complaint_notes.docx'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('processingTitle'), t('processingDesc')),
        _DemoCard(
          title: t('queueTitle'),
          subtitle: t('queueSub'),
          child: Column(
            children: [
              for (final task in tasks)
                _ProcessingRow(
                  isDone: task.$1,
                  title: t(task.$2),
                  detail: task.$3 == 'fingerprintSub' ? t(task.$3) : task.$3,
                  status: t(task.$1 ? 'done' : 'inProgress'),
                ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _DemoCard(
          title: t('quietCheck'),
          subtitle: t('quietSub'),
          child: _Recommendation(text: t('quietBody')),
        ),
        const SizedBox(height: 18),
        _elaReportCard(),
      ],
    );
  }

  Widget _elaReportCard() {
    return _DemoCard(
      title: t('elaTitle'),
      subtitle: t('elaSub'),
      child: Column(
        children: [
          for (final finding in DemoCase.elaFindings)
            _ElaFindingRow(finding: finding, copy: _copy),
          const SizedBox(height: 8),
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: Text(
              t('editRegionCheck'),
              style: const TextStyle(
                color: AppTheme.bark,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          for (final check in DemoCase.elaEditChecks)
            _ElaEditCheckRow(check: check, copy: _copy),
          const SizedBox(height: 10),
          _Recommendation(text: t('elaCaution')),
        ],
      ),
    );
  }

  Widget _classificationStep() {
    final rows = [
      ('threats', 88),
      ('harassment', 74),
      ('doxxing', 52),
      ('impersonation', 23),
      ('hateSpeech', 12),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('classificationTitle'), t('classificationDesc')),
        _DemoCard(
          title: t('patternsTitle'),
          subtitle: t('basedOnItems'),
          child: Column(
            children: [
              for (final row in rows)
                _PatternBar(label: t(row.$1), value: row.$2),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _DemoCard(
          title: t('closerLook'),
          subtitle: t('clusterExample'),
          child: _Recommendation(text: t('clusterText')),
        ),
      ],
    );
  }

  Widget _assessmentStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('assessmentTitle'), t('assessmentDesc')),
        _DemoCard(
          title: t('overallSeverity'),
          subtitle: t('severitySub'),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final badge = Container(
                width: 118,
                height: 118,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    center: Alignment(-.35, -.4),
                    colors: [Color(0xFF9A4A38), Color(0xFF6E2E22)],
                  ),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      t('critical'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Color(0xFFF6EADD),
                        fontFamily: 'Georgia',
                        fontSize: 19,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      t('priorityReview'),
                      style: const TextStyle(
                        color: Color(0xFFE8D5C8),
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              );
              final scale = Column(
                children: [
                  _SeverityRow(t('low'), const Color(0xFFAEB48C)),
                  _SeverityRow(t('medium'), AppTheme.chestnut),
                  _SeverityRow(t('high'), const Color(0xFFA85B3F)),
                  _SeverityRow(t('critical'), AppTheme.brick),
                ],
              );
              if (constraints.maxWidth < 520) {
                return Column(
                  children: [badge, const SizedBox(height: 18), scale],
                );
              }
              return Row(
                children: [
                  badge,
                  const SizedBox(width: 28),
                  Expanded(child: scale),
                ],
              );
            },
          ),
        ),
        const SizedBox(height: 18),
        _twoColumn(
          _DemoCard(
            title: t('legalGrounding'),
            subtitle: t('mappedReference'),
            child: _keyValueList([
              (t('category'), 'PECA 2016'),
              (t('relevantSection'), t('legalSectionValue')),
              (t('reportingBody'), t('fia')),
            ]),
          ),
          _DemoCard(
            title: t('checksTitle'),
            subtitle: t('checksSub'),
            child: _fieldList([
              ('evidenceMatches', 'yes'),
              ('filesOriginal', 'yesUnedited'),
              ('escalating', 'yes'),
              ('repeatedMessages', 'noneFound'),
            ]),
          ),
        ),
        const SizedBox(height: 18),
        _DemoCard(
          title: t('recommendation'),
          child: _Recommendation(text: t('recommendationBody')),
        ),
      ],
    );
  }

  Widget _timelineStep() {
    final events = [
      ('Aug 28, 2026 · 9:14 PM', 'firstContact', 'firstContactDesc', false),
      ('Aug 30, 2026 · 11:02 PM', 'messagesRepeat', 'messagesRepeatDesc', false),
      ('Sep 1, 2026 · 8:47 PM', 'directThreat', 'directThreatDesc', true),
      ('Sep 2, 2026 · 7:20 PM', 'detailsShared', 'detailsSharedDesc', true),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('timelineTitle'), t('timelineDesc')),
        _DemoCard(
          child: Column(
            children: [
              for (int i = 0; i < events.length; i++)
                _TimelineEvent(
                  date: events[i].$1,
                  title: t(events[i].$2),
                  detail: t(events[i].$3),
                  isCritical: events[i].$4,
                  isLast: i == events.length - 1,
                ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _vaultStep() {
    final entries = [
      ('IMG_0231.png', 'addedWhatsApp', Icons.image_outlined, 'WhatsApp'),
      ('instagram_export.json', 'addedInstagram', Icons.forum_outlined, 'Instagram'),
      ('personal_notes.txt', 'addedNotes', Icons.description_outlined, 'Notes'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('vaultTitle'), t('vaultDesc')),
        _DemoCard(
          child: Column(
            children: [
              for (final entry in entries)
                _VaultEntry(
                  filename: entry.$1,
                  subtitle: t(entry.$2),
                  icon: entry.$3,
                  label: entry.$4,
                  expanded: _expandedEvidence.contains(entry.$1),
                  onTap: () {
                    setState(() {
                      if (_expandedEvidence.contains(entry.$1)) {
                        _expandedEvidence.remove(entry.$1);
                      } else {
                        _expandedEvidence.add(entry.$1);
                      }
                    });
                  },
                  copy: _copy,
                ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        Text(
          t('vaultDisclosure'),
          style: const TextStyle(
            color: AppTheme.inkSoft,
            fontSize: 11.5,
            height: 1.5,
          ),
        ),
      ],
    );
  }

  Widget _reportStep() {
    final reportSections = [
      ('summary', 'summaryValue'),
      ('severity', 'severityValue'),
      ('legalReference', 'legalValue'),
      ('evidence', 'evidenceValue'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('reportTitle'), t('reportDesc')),
        _twoColumn(
          _DemoCard(
            title: t('includedTitle'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final item in [
                  'caseSummary',
                  'timeline',
                  'severityNotes',
                  'fingerprints',
                  'nextSteps',
                ])
                  _FieldRow(label: t(item), value: t('included')),
                const SizedBox(height: 14),
                FilledButton.icon(
                  onPressed: () => setState(() => _reportGenerated = true),
                  icon: const Icon(Icons.description_outlined),
                  label: Text(
                    _reportGenerated ? t('reportGenerated') : t('generateReport'),
                  ),
                ),
              ],
            ),
          ),
          _DemoCard(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                color: AppTheme.paper,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppTheme.line),
              ),
              child: _reportGenerated
                  ? Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          t('reportHeading'),
                          style: const TextStyle(
                            fontFamily: 'Georgia',
                            color: AppTheme.bark,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(t('reportPrepared'), style: _smallNoteStyle()),
                        const SizedBox(height: 16),
                        for (final section in reportSections)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: _ReportSection(
                              title: t(section.$1),
                              body: t(section.$2),
                            ),
                          ),
                      ],
                    )
                  : Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 26),
                        child: Column(
                          children: [
                            const Icon(
                              Icons.description_outlined,
                              color: AppTheme.oliveSoft,
                              size: 30,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              t('reportNotGenerated'),
                              textAlign: TextAlign.center,
                              style: _smallNoteStyle(),
                            ),
                          ],
                        ),
                      ),
                    ),
            ),
          ),
        ),
        const SizedBox(height: 18),
        _Disclaimer(text: t('reportDisclaimer')),
      ],
    );
  }

  Widget _supportStep() {
    final replies = [
      ('showAddress', 'addressReply'),
      ('whatToBring', 'bringReply'),
      ('notReady', 'notReadyReply'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('supportTitle'), t('supportDesc')),
        _DemoCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _ChatBubble(text: t('botIntro')),
              _ChatBubble(text: t('userQuestion'), isUser: true),
              _ChatBubble(
                text: '${t('botAnswer')}\n\n${t('officeName')}\n${t('officeSub')}',
              ),
              if (_chatReply case final reply?)
                _ChatBubble(text: reply, isUser: true),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final option in replies)
                    ActionChip(
                      label: Text(t(option.$1)),
                      onPressed: () =>
                          setState(() => _chatReply = t(option.$2)),
                      backgroundColor: AppTheme.sage,
                      side: const BorderSide(color: Color(0xFFCFDBB8)),
                    ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _twoColumn(
          _DemoCard(
            title: t('beforeGoing'),
            child: _fieldList([
              ('reportReady', 'ready'),
              ('validId', 'bringAlong'),
              ('evidenceCopy', 'optional'),
            ]),
          ),
          _DemoCard(
            title: t('needNow'),
            child: _fieldList([
              ('trustedContact', 'notify'),
              ('helpline', 'available24h'),
            ]),
          ),
        ),
      ],
    );
  }

  Widget _safetyStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _pageHeading(t('safetyTitle'), t('safetyDesc')),
        _DemoCard(
          title: t('sosFeature'),
          subtitle: t('alwaysVisible'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _Recommendation(text: t('sosBody')),
              const SizedBox(height: 15),
              FilledButton(
                onPressed: _showSosDialog,
                child: Text(t('tryNow')),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _twoColumn(
          _DemoCard(
            title: t('whoNotified'),
            child: Column(
              children: [
                _FieldRow(label: t('contactOne'), value: t('motherAmina')),
                _FieldRow(label: t('contactTwo'), value: t('friendZara')),
                _FieldRow(label: t('messageSent'), value: t('locationWarning')),
                const SizedBox(height: 10),
                Text(t('manageContacts'), style: _smallNoteStyle()),
              ],
            ),
          ),
          _DemoCard(
            title: t('feelUnsafe'),
            child: Column(
              children: [
                _FieldRow(label: t('nearestPolice'), value: t('shownAutomatically')),
                _FieldRow(label: t('nearestFia'), value: t('shownAutomatically')),
                _FieldRow(label: t('busySpace'), value: t('shownAutomatically')),
                const SizedBox(height: 10),
                Text(t('moveSafe'), style: _smallNoteStyle()),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        _Disclaimer(text: t('emergencyDisclaimer')),
      ],
    );
  }

  Widget _twoColumn(Widget first, Widget second) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 650) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              first,
              const SizedBox(height: 14),
              second,
            ],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: first),
            const SizedBox(width: 20),
            Expanded(child: second),
          ],
        );
      },
    );
  }

  Widget _fieldList(List<(String, String)> items) {
    return Column(
      children: [
        for (int index = 0; index < items.length; index++)
          _FieldRow(
            label: t(items[index].$1),
            value: t(items[index].$2),
            last: index == items.length - 1,
          ),
      ],
    );
  }

  Widget _keyValueList(List<(String, String)> items) {
    return Column(
      children: [
        for (final item in items)
          _FieldRow(label: item.$1, value: item.$2),
      ],
    );
  }

  Widget _stepNavigation() {
    final first = _activeStep == 0;
    final last = _activeStep == DemoCase.steps.length - 1;
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 500;
        final back = first
            ? Text(t('start'), style: _smallNoteStyle())
            : OutlinedButton.icon(
                onPressed: () => _goToStep(_activeStep - 1),
                icon: const Icon(Icons.chevron_left, size: 18),
                label: Text(t('back')),
              );
        final next = last
            ? Text(t('allSteps'), style: _smallNoteStyle())
            : FilledButton.icon(
                onPressed: () => _goToStep(_activeStep + 1),
                icon: const Icon(Icons.chevron_right, size: 18),
                label: Text(
                  '${t('continueTo')} "${t('stepTitle${_activeStep + 1}')}"',
                ),
              );
        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              next,
              const SizedBox(height: 10),
              back,
            ],
          );
        }
        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [back, next],
        );
      },
    );
  }

  Widget _sosButton(bool compact) {
    return Tooltip(
      message: t('sosFeature'),
      child: GestureDetector(
        onDoubleTap: _showSosDialog,
        child: Container(
          width: compact ? 54 : 60,
          height: compact ? 54 : 60,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppTheme.brick,
            border: Border.all(color: AppTheme.brick.withOpacity(.42), width: 5),
            boxShadow: [
              BoxShadow(
                color: AppTheme.brick.withOpacity(.28),
                blurRadius: 18,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: const Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.shield_outlined, color: Color(0xFFF8F1E1), size: 20),
              Text(
                'SOS',
                style: TextStyle(
                  color: Color(0xFFF8F1E1),
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: _isUrdu ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        body: SafeArea(
          child: !_isLoggedIn
              ? (_activeStep == -1 ? _loginScreen() : _noticeScreen())
              : _appScreen(),
        ),
      ),
    );
  }
}

class _LanguageChoice extends StatelessWidget {
  const _LanguageChoice({
    required this.label,
    required this.selected,
    required this.onDark,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final bool onDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(999),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: selected ? AppTheme.dunes : Colors.transparent,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected
                ? AppTheme.bark
                : onDark
                    ? const Color(0xFFB9C29A)
                    : AppTheme.inkSoft,
            fontSize: 11,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class _LoginTab extends StatelessWidget {
  const _LoginTab({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 9),
          decoration: BoxDecoration(
            color: selected ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: AppTheme.bark.withOpacity(.08),
                      blurRadius: 8,
                    ),
                  ]
                : null,
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: selected ? AppTheme.leather : AppTheme.inkSoft,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }
}

class _NoticeItem extends StatelessWidget {
  const _NoticeItem({
    required this.iconText,
    required this.title,
    required this.body,
  });

  final String iconText;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 30,
          height: 30,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppTheme.sage,
            borderRadius: BorderRadius.circular(9),
          ),
          child: Text(iconText, style: const TextStyle(fontSize: 14)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppTheme.bark,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                body,
                style: const TextStyle(
                  color: AppTheme.inkSoft,
                  fontSize: 12.5,
                  height: 1.6,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DemoCard extends StatelessWidget {
  const _DemoCard({required this.child, this.title, this.subtitle});

  final String? title;
  final String? subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 22),
      decoration: BoxDecoration(
        color: AppTheme.paper,
        border: const BorderDirectional(
          start: BorderSide(color: AppTheme.olive, width: 3),
          top: BorderSide(color: AppTheme.line),
          right: BorderSide(color: AppTheme.line),
          bottom: BorderSide(color: AppTheme.line),
        ),
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: AppTheme.bark.withOpacity(.06),
            blurRadius: 18,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (title != null) ...[
            Text(
              title!,
              style: const TextStyle(
                color: AppTheme.bark,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.only(bottom: 15),
                child: Text(
                  subtitle!,
                  style: const TextStyle(
                    color: AppTheme.inkSoft,
                    fontSize: 12.5,
                  ),
                ),
              ),
            ] else
              const SizedBox(height: 12),
          ],
          child,
        ],
      ),
    );
  }
}

class _FieldRow extends StatelessWidget {
  const _FieldRow({
    required this.label,
    required this.value,
    this.last = false,
  });

  final String label;
  final String value;
  final bool last;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 9),
      decoration: BoxDecoration(
        border: last
            ? null
            : const Border(bottom: BorderSide(color: AppTheme.line)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.inkSoft,
                fontSize: 12.5,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(
                color: AppTheme.bark,
                fontSize: 12.5,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProcessingRow extends StatelessWidget {
  const _ProcessingRow({
    required this.isDone,
    required this.title,
    required this.detail,
    required this.status,
  });

  final bool isDone;
  final String title;
  final String detail;
  final String status;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 13),
      child: Row(
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isDone ? AppTheme.olive : AppTheme.sage,
            ),
            child: Icon(
              isDone ? Icons.check : Icons.more_horiz,
              size: 16,
              color: isDone ? Colors.white : AppTheme.oliveDeep,
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppTheme.bark,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  detail,
                  style: const TextStyle(
                    color: AppTheme.inkSoft,
                    fontSize: 11.5,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            status,
            style: const TextStyle(color: AppTheme.inkSoft, fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _ElaFindingRow extends StatelessWidget {
  const _ElaFindingRow({required this.finding, required this.copy});

  final ElaFinding finding;
  final AppCopy copy;

  @override
  Widget build(BuildContext context) {
    final ratio = finding.ratio == null
        ? copy.call('ratioNotProvided')
        : '${finding.ratio!.toStringAsFixed(2)}×';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 11),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.image_outlined, color: AppTheme.olive, size: 19),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  finding.filename,
                  style: const TextStyle(
                    color: AppTheme.bark,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              _Pill(text: finding.format),
            ],
          ),
          const SizedBox(height: 7),
          Wrap(
            spacing: 14,
            runSpacing: 4,
            children: [
              _Metric(label: copy.call('meanError'), value: '${finding.meanError}'),
              _Metric(label: copy.call('p99Error'), value: '${finding.p99Error}'),
              _Metric(label: 'Max', value: '${finding.maxError}'),
              _Metric(label: copy.call('editRatio'), value: ratio),
              _Metric(
                label: 'Size · Q · block',
                value:
                    '${finding.width}×${finding.height} · ${finding.quality} · ${finding.blockSize}',
              ),
            ],
          ),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: Text(
              copy.call('brightestBlocks'),
              style: const TextStyle(
                color: AppTheme.oliveDeep,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
              ),
            ),
            children: [
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: Text(
                  finding.brightestBlocks
                      .map((block) =>
                          '(${block.x}, ${block.y}) · ${block.meanError}')
                      .join('     '),
                  style: const TextStyle(
                    color: AppTheme.inkSoft,
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),
          const Divider(height: 18, color: AppTheme.line),
        ],
      ),
    );
  }
}

class _ElaEditCheckRow extends StatelessWidget {
  const _ElaEditCheckRow({required this.check, required this.copy});

  final ElaEditCheck check;
  final AppCopy copy;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            check.filename,
            style: const TextStyle(
              color: AppTheme.bark,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          Wrap(
            spacing: 14,
            runSpacing: 4,
            children: [
              _Metric(
                label: copy.call('changedRegion'),
                value: '${check.editedMessageError}',
              ),
              _Metric(
                label: copy.call('otherAverage'),
                value: '${check.otherMessagesAverageError}',
              ),
              _Metric(
                label: copy.call('otherMaximum'),
                value: '${check.otherMessagesMaxError}',
              ),
              _Metric(
                label: copy.call('editRatio'),
                value: '${check.ratio.toStringAsFixed(2)}×',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Text.rich(
      TextSpan(
        children: [
          TextSpan(
            text: '$label: ',
            style: const TextStyle(color: AppTheme.inkSoft, fontSize: 11),
          ),
          TextSpan(
            text: value,
            style: const TextStyle(
              color: AppTheme.bark,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.sage,
        border: Border.all(color: const Color(0xFFCFDBB8)),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppTheme.oliveDeep,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _Recommendation extends StatelessWidget {
  const _Recommendation({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppTheme.sage2,
        borderRadius: BorderRadius.circular(10),
        border: const BorderDirectional(
          start: BorderSide(color: AppTheme.olive, width: 3),
        ),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppTheme.bark,
          fontSize: 12.5,
          height: 1.7,
        ),
      ),
    );
  }
}

class _Disclaimer extends StatelessWidget {
  const _Disclaimer({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
      decoration: BoxDecoration(
        color: AppTheme.sage2,
        border: Border.all(color: const Color(0xFFD9E2C6)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, color: AppTheme.oliveDeep, size: 17),
          const SizedBox(width: 9),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: AppTheme.inkSoft,
                fontSize: 12,
                height: 1.55,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PatternBar extends StatelessWidget {
  const _PatternBar({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 11),
      child: Row(
        children: [
          SizedBox(
            width: 145,
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.bark,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: value / 100,
                minHeight: 8,
                backgroundColor: AppTheme.sage,
                valueColor: const AlwaysStoppedAnimation(AppTheme.olive),
              ),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 38,
            child: Text(
              '$value%',
              textAlign: TextAlign.end,
              style: const TextStyle(color: AppTheme.inkSoft, fontSize: 12.5),
            ),
          ),
        ],
      ),
    );
  }
}

class _SeverityRow extends StatelessWidget {
  const _SeverityRow(this.label, this.color);

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 70,
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.inkSoft,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(7),
              child: LinearProgressIndicator(
                value: 1,
                minHeight: 14,
                backgroundColor: AppTheme.sage,
                valueColor: AlwaysStoppedAnimation(color),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TimelineEvent extends StatelessWidget {
  const _TimelineEvent({
    required this.date,
    required this.title,
    required this.detail,
    required this.isCritical,
    required this.isLast,
  });

  final String date;
  final String title;
  final String detail;
  final bool isCritical;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final dotColor = isCritical ? AppTheme.brick : AppTheme.chestnut;
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 24,
            child: Column(
              children: [
                Container(
                  width: 13,
                  height: 13,
                  margin: const EdgeInsets.only(top: 4),
                  decoration: BoxDecoration(
                    color: dotColor,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                    boxShadow: [BoxShadow(color: dotColor, spreadRadius: .5)],
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 1.5,
                      color: AppTheme.line,
                      margin: const EdgeInsets.symmetric(vertical: 3),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: isLast ? 0 : 23),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    date,
                    textDirection: TextDirection.ltr,
                    style: const TextStyle(
                      color: AppTheme.inkSoft,
                      fontSize: 11.5,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    title,
                    style: const TextStyle(
                      color: AppTheme.bark,
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    detail,
                    style: const TextStyle(
                      color: AppTheme.inkSoft,
                      fontSize: 12.5,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _VaultEntry extends StatelessWidget {
  const _VaultEntry({
    required this.filename,
    required this.subtitle,
    required this.icon,
    required this.label,
    required this.expanded,
    required this.onTap,
    required this.copy,
  });

  final String filename;
  final String subtitle;
  final IconData icon;
  final String label;
  final bool expanded;
  final VoidCallback onTap;
  final AppCopy copy;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: AppTheme.sage,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: AppTheme.oliveDeep),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    filename,
                    style: const TextStyle(
                      color: AppTheme.bark,
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: AppTheme.inkSoft,
                      fontSize: 11.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    copy.call('demoPreview'),
                    style: const TextStyle(
                      color: AppTheme.oliveDeep,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: .4,
                    ),
                  ),
                  if (expanded) ...[
                    const Divider(height: 16, color: AppTheme.line),
                    if (label == 'WhatsApp')
                      for (final message in [
                        'Why are you ignoring my texts?',
                        'I know where you work. Be careful.',
                        'Please stop messaging me.',
                        'This is not over.',
                      ])
                        _ChatBubble(text: message)
                    else if (label == 'Instagram')
                      for (final message in [
                        'Everyone should see what kind of person you really are.',
                        'Your home address is not hard to find.',
                        'Nowhere to hide now.',
                      ])
                        _ChatBubble(text: message)
                    else
                      _ChatBubble(
                        text:
                            'I started keeping a record after the first message so I could remember what happened.',
                      ),
                    const SizedBox(height: 6),
                    Text(
                      copy.call('unchanged'),
                      style: const TextStyle(
                        color: AppTheme.inkSoft,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            Icon(
              expanded ? Icons.expand_less : Icons.expand_more,
              color: AppTheme.oliveDeep,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}

class _ReportSection extends StatelessWidget {
  const _ReportSection({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: AppTheme.bark,
            fontSize: 12.5,
            fontWeight: FontWeight.w600,
          ),
        ),
        Text(
          body,
          style: const TextStyle(
            color: AppTheme.inkSoft,
            fontSize: 12.5,
            height: 1.7,
          ),
        ),
      ],
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.text, this.isUser = false});

  final String text;
  final bool isUser;

  @override
  Widget build(BuildContext context) {
    final bubble = Container(
      constraints: const BoxConstraints(maxWidth: 520),
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 11),
      decoration: BoxDecoration(
        color: isUser ? AppTheme.leather : AppTheme.sage2,
        borderRadius: BorderRadiusDirectional.only(
          topStart: const Radius.circular(14),
          topEnd: const Radius.circular(14),
          bottomStart: Radius.circular(isUser ? 14 : 4),
          bottomEnd: Radius.circular(isUser ? 4 : 14),
        ),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: isUser ? const Color(0xFFF8F1E1) : AppTheme.bark,
          fontSize: 12.5,
          height: 1.6,
        ),
      ),
    );
    return Align(
      alignment: isUser ? AlignmentDirectional.centerEnd : AlignmentDirectional.centerStart,
      child: bubble,
    );
  }
}

class _SosDialog extends StatefulWidget {
  const _SosDialog({required this.copy});

  final AppCopy copy;

  @override
  State<_SosDialog> createState() => _SosDialogState();
}

class _SosDialogState extends State<_SosDialog> {
  bool _showPlaces = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer(const Duration(milliseconds: 1000), () {
      if (mounted) setState(() => _showPlaces = true);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String t(String key) => widget.copy.call(key);

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(20),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 28),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: const BoxDecoration(
                    color: AppTheme.sage,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.favorite_border,
                    color: AppTheme.oliveDeep,
                    size: 28,
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  t(_showPlaces ? 'sharedStatus' : 'sendingLocation'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppTheme.bark,
                    fontFamily: 'Georgia',
                    fontSize: 19,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  t('alertingContacts'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppTheme.inkSoft,
                    fontSize: 13,
                    height: 1.6,
                  ),
                ),
                if (_showPlaces) ...[
                  const SizedBox(height: 16),
                  Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: Text(
                      t('nearbyPlaces'),
                      style: const TextStyle(
                        color: AppTheme.bark,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  _SafePlace(t('fiaCentre'), t('aabpara'), '0.8 km'),
                  _SafePlace(t('policeStation'), t('open24h'), '1.1 km'),
                  _SafePlace(t('shifaHospital'), t('emergencyWard'), '2.4 km'),
                  _SafePlace(t('centaurus'), t('publicPlace'), '1.6 km'),
                ] else ...[
                  const SizedBox(height: 12),
                  const LinearProgressIndicator(
                    color: AppTheme.olive,
                    backgroundColor: AppTheme.sage,
                  ),
                ],
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text(t('close')),
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  t('sosDisclaimer'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppTheme.inkSoft,
                    fontSize: 11,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SafePlace extends StatelessWidget {
  const _SafePlace(this.name, this.detail, this.distance);

  final String name;
  final String detail;
  final String distance;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppTheme.line)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    color: AppTheme.bark,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  detail,
                  style: const TextStyle(
                    color: AppTheme.inkSoft,
                    fontSize: 11.5,
                  ),
                ),
              ],
            ),
          ),
          Text(
            distance,
            textDirection: TextDirection.ltr,
            style: const TextStyle(
              color: AppTheme.oliveDeep,
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
