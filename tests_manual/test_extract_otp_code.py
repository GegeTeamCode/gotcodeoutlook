"""Kiểm tra extract_otp_code với các mẫu mail thật đã gặp.

Chạy: python3 tests_manual/test_extract_otp_code.py
Không cần mạng, không cần accounts.db — chỉ import hàm thuần từ api_server.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api_server import extract_otp_code  # noqa: E402

BATTLENET_SENDER = '"Battle.net" <noreply@battle.net>'

# Mail Battle.net bản tiếng Hàn (account region KR) — nhãn "인증번호", mã nằm
# một mình trong thẻ <em>.
KO_BODY = (
    '<table><tr><td style="font-weight: 700;">인증번호: </td></tr></table>\r\n'
    '<p style=" "><em style="font-size: 28px;">FS7XCB</em></p>\r\n'
    '<p style=" "> ngo 님, 안녕하세요!</p>\r\n'
    '<p style=" "> Battle.net 계정 본인 확인 메일입니다.</p>'
)
KO_SUBJECT = 'Battle.net 계정 인증'

EN_BODY = (
    "<p>Hi,</p><p>Here's your security code: <b>G6MJTJ</b></p>"
    "<p>Battle.net Account Verification</p>"
)

# Nhãn chưa có trong danh sách (giả lập Blizzard đổi/thêm ngôn ngữ) — phải rơi
# xuống nhánh dò theo cấu trúc và vẫn ra mã.
UNKNOWN_LABEL_BODY = (
    '<p>Battle.net</p><table><tr><td>Kode keamanan:</td></tr></table>'
    '<p><em>H4KD9Q</em></p>'
)

POE_BODY = "<p>Your code is cfa-808-6def, it expires in 10 minutes.</p>"

# Mail "Cảnh báo bảo mật" của Google chứa TÊN App Password có dấu gạch, đúng
# định dạng mã PoE -> không được trả về.
GOOGLE_ALERT_BODY = (
    '<p>Ứng dụng gege-otp-113 đã được cấp quyền truy cập vào Tài khoản Google '
    'của bạn.</p>'
)
GOOGLE_SENDER = 'Google <no-reply@accounts.google.com>'

STEAM_SENDER = '"Steam" <noreply@steampowered.com>'
# Ma mot minh tren dong (template nhieu dong).
STEAM_MULTILINE = (
    '<td>Here is the Steam Guard code you need to login to account acc123:</td>\r\n'
    '<td style="font-size:48px; font-family:Arial, \'Motiva Sans\';">\r\n  7KQ4M   </td>\r\n'
    '<td>Login attempt from a computer located at 1.2.3.4 (VN).</td>'
)
# Exchange/Graph tra HTML don 1 dong.
STEAM_MINIFIED = (
    '<html><body><table><tr><td>Login Code</td></tr><tr><td style="font-size:48px">7KQ4M</td></tr>'
    '<tr><td>Request made from Vietnam</td></tr></table>'
    '<a href="https://store.steampowered.com">Steam</a></body></html>'
)
# Ma toan chu (bang chu Steam khong co nguyen am) + &nbsp; dinh sau ma.
STEAM_ALL_LETTERS = '<td>Login Code</td><td>KFMWV&nbsp;</td> <p>Steam Support</p>'
STEAM_PLAIN = (
    'Dear acc123,\r\n\r\nHere is the Steam Guard code you need to login to '
    'account acc123:\r\n\r\n7KQ4M\r\n\r\nThe Steam Support Team'
)
STEAM_PLAIN_INLINE = 'Your Steam Guard code: 7KQ4M (Steam Support)'
# Mail thong bao khong co ma - khong duoc tra tu 5 ky tu bat ky ("email", "STEAM"...).
STEAM_NO_CODE = (
    '<p>New sign in to Steam</p><p>Your Steam Guard code was used to sign in from a new '
    'device. Check your email and CLICK here.</p><p>STEAM</p><p>98009</p>'
)


def check(label, got, want):
    status = "OK " if got == want else "FAIL"
    print(f"[{status}] {label}: got={got} want={want}")
    return got == want


def main():
    results = [
        check("KR body + game=diablo", extract_otp_code(KO_BODY, 'diablo', BATTLENET_SENDER), ['FS7XCB']),
        check("KR body + game=Diablo 4", extract_otp_code(KO_BODY, 'Diablo 4', BATTLENET_SENDER), ['FS7XCB']),
        check("KR body + game=None", extract_otp_code(KO_BODY, None, BATTLENET_SENDER), ['FS7XCB']),
        check("KR body + game=poe (khong tra ma Diablo)", extract_otp_code(KO_BODY, 'poe', BATTLENET_SENDER), []),
        check("KR subject khong chua ma", extract_otp_code(KO_SUBJECT, 'diablo', BATTLENET_SENDER), []),
        check("EN body", extract_otp_code(EN_BODY, 'diablo', BATTLENET_SENDER), ['G6MJTJ']),
        check("Nhan la -> do theo cau truc", extract_otp_code(UNKNOWN_LABEL_BODY, 'diablo', BATTLENET_SENDER), ['H4KD9Q']),
        check("PoE van chay", extract_otp_code(POE_BODY, 'poe'), ['cfa-808-6def']),
        check("Google alert khong tra ten app password",
              extract_otp_code(GOOGLE_ALERT_BODY, None, GOOGLE_SENDER), []),
        check("Mail thuong khong phai Battle.net khong bi quet bua",
              extract_otp_code('<p>Order #ABC123 delivered</p>', 'diablo', 'G2G <noreply@g2g.com>'), []),
        check("Steam: ma mot minh tren dong", extract_otp_code(STEAM_MULTILINE, 'steam', STEAM_SENDER), ['7KQ4M']),
        check("Steam: HTML don 1 dong", extract_otp_code(STEAM_MINIFIED, 'steam', STEAM_SENDER), ['7KQ4M']),
        check("Steam: ma toan chu + &nbsp;", extract_otp_code(STEAM_ALL_LETTERS, 'steam', STEAM_SENDER), ['KFMWV']),
        check("Steam: mail thuan text", extract_otp_code(STEAM_PLAIN, 'steam', STEAM_SENDER), ['7KQ4M']),
        check("Steam: ma cung dong voi nhan", extract_otp_code(STEAM_PLAIN_INLINE, 'steam', STEAM_SENDER), ['7KQ4M']),
        check("Steam: game=None van ra ma", extract_otp_code(STEAM_MINIFIED, None, STEAM_SENDER), ['7KQ4M']),
        check("Steam: mail thong bao khong co ma", extract_otp_code(STEAM_NO_CODE, 'steam', STEAM_SENDER), []),
        check("Steam: game=diablo khong tra ma Steam", extract_otp_code(STEAM_MINIFIED, 'diablo', STEAM_SENDER), []),
        check("Steam: mail khong phai Steam khong bi quet",
              extract_otp_code('<p>Order</p><p>7KQ4M</p>', 'steam', 'G2G <noreply@g2g.com>'), []),
    ]
    print()
    if all(results):
        print(f"Tat ca {len(results)} truong hop dat.")
        return 0
    print(f"{results.count(False)}/{len(results)} truong hop KHONG dat.")
    return 1


if __name__ == '__main__':
    sys.exit(main())
