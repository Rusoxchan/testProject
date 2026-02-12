import 'dart:io';
import 'package:flutter/material.dart';
import 'package:youtube_explode_dart/youtube_explode_dart.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Video Downloader',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF89b4fa),
          brightness: Brightness.dark,
          background: const Color(0xFF1e1e2e),
          surface: const Color(0xFF1e1e2e),
        ),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF1e1e2e),
        cardColor: const Color(0xFF313244),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Color(0xFFcdd6f4)),
        ),
      ),
      home: const DownloadPage(),
    );
  }
}

class DownloadPage extends StatefulWidget {
  const DownloadPage({super.key});

  @override
  State<DownloadPage> createState() => _DownloadPageState();
}

class _DownloadPageState extends State<DownloadPage> {
  final TextEditingController _urlController = TextEditingController();
  String _status = "Ready";
  bool _isDownloading = false;
  double _progress = 0.0;
  String? _lastFilePath;

  Future<void> _downloadVideo() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      _showSnack("Please enter a URL");
      return;
    }

    // Request permissions
    var status = await Permission.storage.request();
    if (status.isDenied) {
      // Try manage external storage for Android 11+
      status = await Permission.manageExternalStorage.request();
    }
    
    if (status.isPermanentlyDenied) {
      _showSnack("Permission denied. Enable in Settings.");
      openAppSettings();
      return;
    }

    setState(() {
      _isDownloading = true;
      _status = "Getting video info...";
      _progress = 0.0;
    });

    final yt = YoutubeExplode();
    try {
      var video = await yt.videos.get(url);
      setState(() => _status = "Found: ${video.title}");

      // Get manifest
      var manifest = await yt.videos.streamsClient.getManifest(video.id);
      var streamInfo = manifest.muxed.withHighestBitrate();

      setState(() => _status = "Downloading...");

      // Get stream
      var stream = yt.videos.streamsClient.get(streamInfo);

      // File path
      Directory? dir;
      if (Platform.isAndroid) {
        dir = Directory('/storage/emulated/0/Download');
      } else {
        dir = await getApplicationDocumentsDirectory();
      }

      if (!await dir.exists()) {
        dir = await getExternalStorageDirectory(); // Fallback
      }

      var fileName = "${video.title}.mp4".replaceAll(RegExp(r'[^\w\s\.]'), '_');
      var filePath = "${dir!.path}/$fileName";
      var file = File(filePath);
      var fileStream = file.openWrite();

      var len = streamInfo.size.totalBytes;
      var count = 0;

      await stream.listen((data) {
        count += data.length;
        var p = count / len;
        if (p > _progress + 0.05) {
          setState(() => _progress = p);
        }
        fileStream.add(data);
      }).asFuture();

      await fileStream.flush();
      await fileStream.close();

      setState(() {
        _status = "Downloaded to Downloads!";
        _isDownloading = false;
        _progress = 1.0;
        _lastFilePath = filePath;
      });

      _showSnack("Download Complete!");
      
      // Try to open it
      // OpenFile.open(filePath);

    } catch (e) {
      setState(() {
        _status = "Error: $e";
        _isDownloading = false;
      });
      _showSnack("Error: $e");
    } finally {
      yt.close();
    }
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Video Downloader"),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.download_rounded, size: 64, color: Color(0xFF89b4fa)),
            const SizedBox(height: 32),
            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                labelText: "YouTube URL",
                filled: true,
                fillColor: const Color(0xFF313244),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                prefixIcon: const Icon(Icons.link, color: Color(0xFFa6adc8)),
              ),
              style: const TextStyle(color: Colors.white),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isDownloading ? null : _downloadVideo,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF89b4fa),
                foregroundColor: const Color(0xFF1e1e2e),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: _isDownloading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1e1e2e)),
                    )
                  : const Text("Download", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 24),
            Text(
              _status,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFa6adc8)),
            ),
            if (_isDownloading)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: LinearProgressIndicator(
                  value: _progress,
                  backgroundColor: const Color(0xFF313244),
                  color: const Color(0xFFa6e3a1),
                ),
              ),
            if (!_isDownloading && _lastFilePath != null)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: TextButton.icon(
                  onPressed: () => OpenFile.open(_lastFilePath),
                  icon: const Icon(Icons.play_arrow),
                  label: const Text("Open File"),
                ),
              )
          ],
        ),
      ),
    );
  }
}
