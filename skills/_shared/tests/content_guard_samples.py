"""Fictional negative samples for the content guard, one per category (1-7).

Every sample is assembled from pieces so this file itself does not trip a leak scanner.
SECRET_TEXT is the part that must never be echoed back by the guard.
"""
SECRET_TEXT = "s3cret" + "PW99"
SAMPLES = {
    "vi": "画面の文言を確認する（c\u1ea7n s\u1eeda）",  # Vietnamese words, kept as escapes
    "ctrl": "色付きの出力\x1b[31m赤字",
    "path": "手順は " + "plans" + "/260101-0000-sample/phase-01.md を参照",
    "secret": "接続先 " + "postgres://app:" + SECRET_TEXT + "@db.internal:5432/app",
    "email": "連絡先は taro.yamada" + "@" + "corp-sample.co.jp まで",
    "term": "LAB" + "-3 の" + "採" + "点で判明した不具合",
    "internal": "資料: https://" + "drive.google.com" + "/file/d/abc123/view",
}
