from chromecookie.chrome_cookie import ChromeCookieJar
import os


if __name__ == '__main__':
    profile = 'Profile 2'
    cookie_file_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\{}\Cookies'.format(profile))
    jar = ChromeCookieJar(filename=cookie_file_path, url='game.granbluefantasy.jp')
    jar.load()
    for cookie in jar:
        print(vars(cookie))
