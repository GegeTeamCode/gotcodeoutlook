"""Kiểm tra extract_otp_code với các mẫu mail thật đã gặp.

Chạy: python3 tests_manual/test_extract_otp_code.py
Không cần mạng, không cần accounts.db — chỉ import hàm thuần từ api_server.
"""
import re
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

STEAM_SENDER = 'Steam Support <noreply@steampowered.com>'
# Trich tu mail that "Your Steam account: Access from new computer" (ten account
# va quoc gia da doi). Luu y: ban HTML KHONG co nhan "Login Code" - ngay truoc o
# chua ma la ten quoc gia.
STEAM_HTML = (
    '<td class="title-36 pb-30 c-grey6 fw-b" style="font-size:36px;">\n\t\t\tacc123,\t\t</td>\n'
    '<td style="font-size:18px;">\n\t\t\tIt looks like you are trying to log in from a new device. '
    'Here is the Steam Guard code you need to access your account:\t\t</td>\n'
    '<table width="100%" border="0" cellspacing="0" cellpadding="0">\n\t<tr>\n'
    '\t\t<td style="font-size:18px; line-height:25px; font-family:Arial, sans-serif, \'Motiva Sans\'; '
    'color:#8f98a0; text-align:center;">\n\t\t\tRequest made from\t\t</td>\n\t</tr>\n\t<tr>\n'
    '\t\t<td style="font-size:25px; color:#f1f1f1; text-align:center;letter-spacing:1px">\n'
    '\t\t\tVietnam\t\t</td>\n\t</tr>\n\t<tr>\n\t\t<td style="padding-bottom: 16px"></td>\n\t</tr>\n\t<tr>\n'
    '\t\t<td class="title-48 c-blue1 fw-b a-center" style="font-size:48px; line-height:52px; '
    'font-family:Arial, sans-serif, \'Motiva Sans\'; color:#3a9aed; font-weight:bold; text-align:center;">\n'
    '\t\t\tCY2QG\t\t</td>\n\t</tr>\n</table>\n'
    '<td>If this wasn\'t you</td>\n<td>The login code contained in this email is required to access '
    'your account.</td>\n<td>PO Box 1688 Bellevue, WA 98009</td>\n'
    '<a href="https://help.steampowered.com">https://help.steampowered.com</a>'
)


def exchange_like(body):
    """Gia lap HTML do Exchange/Graph tra ve: bo khoang trang giua cac the, don
    het ve 1 dong, them tien to x_ vao class."""
    flat = re.sub(r'>\s+<', '><', body)
    return re.sub(r'\s+', ' ', flat).replace('class="', 'class="x_')


# Ban text/plain cua cung mail do (duong IMAP uu tien text/plain).
STEAM_TEXT = (
    'Dear acc123,\n\nIt looks like you are trying to log in from a new device. Here is the Steam\n'
    'Guard code you need to access your account:\n\nRequest made from\nVietnam\n\nLogin Code\nCY2QG\n\n\n\n'
    'If this wasn\'t you\n\nThe login code contained in this email is required to access your account.\n'
    'https://help.steampowered.com\n'
)
# Template cu hon (van con gap).
STEAM_TEXT_OLD = (
    'Dear acc123,\nHere is the Steam Guard code you need to login to account acc123:\n\n6VCC5\n'
    'This email was generated because of a login attempt from a web or mobile device located at '
    '1.2.3.4 (VN).\n\nThe Steam Team\nhttps://help.steampowered.com\n'
)
# body_preview: toan bo noi dung nam tren 1 dong.
STEAM_PREVIEW = (
    'Dear acc123, It looks like you are trying to log in from a new device. Here is the Steam Guard '
    'code you need to access your account: Request made from Vietnam Login Code CY2QG If this wasn\'t you'
)
# Mail thong bao khong co ma - khong duoc tra tu 5 ky tu bat ky ("email", "STEAM"...).
STEAM_NO_CODE = (
    '<td class="title-48 c-blue1">New sign in to Steam</td><p>Your Steam Guard code was used to sign '
    'in from a new device. Check your email and CLICK here.</p><p>STEAM</p><p>98009</p>'
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
        check("Steam: HTML mail that", extract_otp_code(STEAM_HTML, 'steam', STEAM_SENDER), ['CY2QG']),
        check("Steam: HTML kieu Exchange (don 1 dong, class x_)",
              extract_otp_code(exchange_like(STEAM_HTML), 'steam', STEAM_SENDER), ['CY2QG']),
        check("Steam: CRLF + &nbsp; canh ma",
              extract_otp_code(STEAM_HTML.replace('CY2QG', 'CY2QG&nbsp;').replace('\n', '\r\n'), 'steam', STEAM_SENDER),
              ['CY2QG']),
        check("Steam: ma toan chu", extract_otp_code(exchange_like(STEAM_HTML.replace('CY2QG', 'KFMWV')), 'steam', STEAM_SENDER), ['KFMWV']),
        check("Steam: ma ngoai bang chu van lay duoc tu o chua ma",
              extract_otp_code(exchange_like(STEAM_HTML.replace('CY2QG', 'S0L1Z')), 'steam', STEAM_SENDER), ['S0L1Z']),
        check("Steam: text/plain", extract_otp_code(STEAM_TEXT, 'steam', STEAM_SENDER), ['CY2QG']),
        check("Steam: text/plain CRLF, ma ngoai bang chu (sau nhan Login Code)",
              extract_otp_code(STEAM_TEXT.replace('CY2QG', 'S0L1Z').replace('\n', '\r\n'), 'steam', STEAM_SENDER), ['S0L1Z']),
        check("Steam: template cu", extract_otp_code(STEAM_TEXT_OLD, 'steam', STEAM_SENDER), ['6VCC5']),
        check("Steam: body_preview 1 dong", extract_otp_code(STEAM_PREVIEW, 'steam', STEAM_SENDER), ['CY2QG']),
        check("Steam: game=None van ra ma", extract_otp_code(exchange_like(STEAM_HTML), None, STEAM_SENDER), ['CY2QG']),
        check("Steam: tieu de mail khong chua ma",
              extract_otp_code('Your Steam account: Access from new computer', 'steam', STEAM_SENDER), []),
        check("Steam: mail thong bao khong co ma", extract_otp_code(STEAM_NO_CODE, 'steam', STEAM_SENDER), []),
        check("Steam: game=diablo khong tra ma Steam", extract_otp_code(STEAM_HTML, 'diablo', STEAM_SENDER), []),
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
