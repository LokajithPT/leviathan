import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';

void main() {
  runApp(MaterialApp(
    home: MemoryGame(),
    debugShowCheckedModeBanner: false,
  ));
}

class MemoryGame extends StatefulWidget {
  @override
  _MemoryGameState createState() => _MemoryGameState();
}

class _MemoryGameState extends State<MemoryGame> {
  final List<Color> tileColors = [
    Colors.redAccent,
    Colors.greenAccent,
    Colors.blueAccent,
    Colors.amberAccent,
  ];

  List<int> sequence = [];
  List<int> playerInput = [];
  bool inputEnabled = false;
  int currentLevel = 1;

  Map<int, bool> flashing = {0: false, 1: false, 2: false, 3: false};

  @override
  void initState() {
    super.initState();
    _startGame();
  }

  void _startGame() {
    sequence.clear();
    playerInput.clear();
    currentLevel = 1;
    _nextRound();
  }

  void _nextRound() async {
    inputEnabled = false;
    playerInput.clear();
    sequence.add(Random().nextInt(4));
    await _playSequence();
    inputEnabled = true;
  }

  Future<void> _playSequence() async {
    for (int index in sequence) {
      setState(() => flashing[index] = true);
      await Future.delayed(Duration(milliseconds: 400));
      setState(() => flashing[index] = false);
      await Future.delayed(Duration(milliseconds: 250));
    }
  }

  Future<void> _flashOnTap(int index) async {
    setState(() => flashing[index] = true);
    await Future.delayed(Duration(milliseconds: 200));
    setState(() => flashing[index] = false);
  }

  void _handleTap(int index) async {
    if (!inputEnabled) return;
    await _flashOnTap(index);
    playerInput.add(index);
    if (playerInput[playerInput.length - 1] != sequence[playerInput.length - 1]) {
      _showGameOver();
      return;
    }
    if (playerInput.length == sequence.length) {
      currentLevel++;
      _nextRound();
    }
  }

  void _showGameOver() {
    inputEnabled = false;
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: Color(0xFF2D2A40),
        title: Text('Game Over', style: TextStyle(color: Colors.white)),
        content: Text('You reached level $currentLevel',
            style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _startGame();
            },
            child: Text('Restart', style: TextStyle(color: Colors.purpleAccent)),
          ),
        ],
      ),
    );
  }

  Widget _buildTile(int index) {
    return GestureDetector(
      onTap: () => _handleTap(index),
      child: AnimatedOpacity(
        duration: Duration(milliseconds: 200),
        opacity: flashing[index]! ? 1.0 : 0.6,
        child: Container(
          margin: EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: tileColors[index],
            borderRadius: BorderRadius.circular(20),
            boxShadow: flashing[index]!
                ? [
                    BoxShadow(
                      color: tileColors[index].withOpacity(0.8),
                      blurRadius: 25,
                      spreadRadius: 5,
                    ),
                  ]
                : [],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF1E1B2E), // Warm dark background
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: Text(
          'Memory Game',
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
        ),
        centerTitle: true,
      ),
      body: Column(
        children: [
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              children: List.generate(4, (index) => _buildTile(index)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20.0),
            child: Text(
              'Level: $currentLevel',
              style: TextStyle(fontSize: 24, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

}
