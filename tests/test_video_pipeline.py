import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import skipUnless
from django.test import TestCase, override_settings
from courses.models import Course, Lesson
from videos.models import Video
from videos.views import _convert_to_hls

@skipUnless(shutil.which('ffmpeg'), 'FFmpeg is required for the conversion integration test')
class VideoPipelineTests(TestCase):
    def test_real_ffmpeg_generates_playable_hls_variants(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=Path(directory)):
            source=Path(directory)/'source.mp4'
            subprocess.run(['ffmpeg','-f','lavfi','-i','color=c=green:s=320x180:r=24','-f','lavfi','-i','sine=frequency=440:sample_rate=44100','-t','2','-c:v','libx264','-c:a','aac','-pix_fmt','yuv420p',str(source),'-y'],check=True,capture_output=True,timeout=30)
            course=Course.objects.create(title='Test',slug='test',is_published=True)
            lesson=Lesson.objects.create(course=course,title='Video',is_published=True)
            video=Video.objects.create(lesson=lesson)
            _convert_to_hls(video,str(source),lesson.pk)
            video.refresh_from_db();lesson.refresh_from_db()
            self.assertEqual(video.status,'ready')
            self.assertTrue(video.has_360p and video.has_720p and video.has_1080p)
            self.assertEqual(lesson.duration_seconds,2)
            master=Path(directory)/video.hls_path/'master.m3u8'
            self.assertTrue(master.is_file())
            for quality in ['360p','720p','1080p']:
                playlist=master.parent/quality/'index.m3u8'
                self.assertIn('#EXT-X-ENDLIST',playlist.read_text())
                result=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height','-of','csv=p=0',str(playlist)],capture_output=True,text=True,check=True,timeout=20)
                self.assertIn({'360p':'640,360','720p':'1280,720','1080p':'1920,1080'}[quality],result.stdout)
