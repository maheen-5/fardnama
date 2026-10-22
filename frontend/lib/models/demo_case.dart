class DemoStep {
  const DemoStep(this.title, this.description);

  final String title;
  final String description;
}

class ElaFinding {
  const ElaFinding({
    required this.filename,
    required this.format,
    required this.meanError,
    required this.p99Error,
    required this.maxError,
    required this.ratio,
    required this.width,
    required this.height,
    required this.quality,
    required this.blockSize,
    required this.brightestBlocks,
  });

  final String filename;
  final String format;
  final double meanError;
  final double p99Error;
  final int maxError;
  final double? ratio;
  final int width;
  final int height;
  final int quality;
  final int blockSize;
  final List<ElaBlock> brightestBlocks;
}

class ElaBlock {
  const ElaBlock(this.x, this.y, this.meanError);

  final int x;
  final int y;
  final int meanError;
}

class ElaEditCheck {
  const ElaEditCheck({
    required this.filename,
    required this.editedMessageError,
    required this.otherMessagesAverageError,
    required this.otherMessagesMaxError,
    required this.ratio,
  });

  final String filename;
  final double editedMessageError;
  final double otherMessagesAverageError;
  final double otherMessagesMaxError;
  final double ratio;
}

abstract final class DemoCase {
  static const caseNumber = 'FN-2291';

  static const steps = [
    DemoStep('Add evidence', 'Bring in screenshots, chats or files'),
    DemoStep('Read & organize', 'Text is pulled from every file'),
    DemoStep('Understand what happened', 'Patterns are named and grouped'),
    DemoStep('Assessment', 'Severity and legal grounding, together'),
    DemoStep('Timeline', 'Everything laid out in order'),
    DemoStep('Evidence vault', 'Everything kept safe, unchanged'),
    DemoStep('Build report', 'One clear document, ready to share'),
    DemoStep('Get support', 'Guidance for what to do next'),
    DemoStep('Safety tools', 'Quick help if you feel unsafe'),
  ];

  static const elaFindings = [
    ElaFinding(
      filename: 'jpeg_original.jpg',
      format: 'JPEG',
      meanError: 0.143,
      p99Error: 3,
      maxError: 11,
      ratio: null,
      width: 540,
      height: 960,
      quality: 90,
      blockSize: 16,
      brightestBlocks: [
        ElaBlock(304, 48, 3),
        ElaBlock(288, 48, 3),
        ElaBlock(272, 48, 3),
        ElaBlock(272, 32, 3),
        ElaBlock(256, 48, 3),
      ],
    ),
    ElaFinding(
      filename: 'jpeg_resaved.jpg',
      format: 'JPEG',
      meanError: 0.086,
      p99Error: 1,
      maxError: 8,
      ratio: 2.05,
      width: 540,
      height: 960,
      quality: 90,
      blockSize: 16,
      brightestBlocks: [
        ElaBlock(272, 48, 2),
        ElaBlock(256, 48, 2),
        ElaBlock(256, 32, 2),
        ElaBlock(240, 48, 2),
        ElaBlock(224, 48, 2),
      ],
    ),
    ElaFinding(
      filename: 'jpeg_edited.jpg',
      format: 'JPEG',
      meanError: 0.096,
      p99Error: 2,
      maxError: 8,
      ratio: 4.08,
      width: 540,
      height: 960,
      quality: 90,
      blockSize: 16,
      brightestBlocks: [
        ElaBlock(272, 48, 2),
        ElaBlock(256, 48, 2),
        ElaBlock(256, 32, 2),
        ElaBlock(240, 48, 2),
        ElaBlock(224, 48, 2),
      ],
    ),
    ElaFinding(
      filename: 'original.png',
      format: 'PNG',
      meanError: 0.739,
      p99Error: 9,
      maxError: 32,
      ratio: null,
      width: 540,
      height: 960,
      quality: 90,
      blockSize: 16,
      brightestBlocks: [
        ElaBlock(304, 48, 8),
        ElaBlock(288, 48, 7),
        ElaBlock(176, 48, 7),
        ElaBlock(160, 48, 7),
        ElaBlock(128, 48, 7),
      ],
    ),
  ];

  static const elaEditChecks = [
    ElaEditCheck(
      filename: 'jpeg_resaved.jpg',
      editedMessageError: 0.134,
      otherMessagesAverageError: 0.066,
      otherMessagesMaxError: 0.14,
      ratio: 2.05,
    ),
    ElaEditCheck(
      filename: 'jpeg_edited.jpg',
      editedMessageError: 0.267,
      otherMessagesAverageError: 0.066,
      otherMessagesMaxError: 0.14,
      ratio: 4.08,
    ),
  ];
}
