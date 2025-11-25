import os
import sys
import pygame as pg
import random
from pygame.transform import rotozoom


WIDTH, HEIGHT = 1100, 650
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DELTA = {
    pg.K_UP: (0, -5), 
    pg.K_DOWN: (0, 5), 
    pg.K_LEFT: (-5, 0), 
    pg.K_RIGHT: (5, 0),
}

def check_bound(rct):
    """
    画面内or画面外を判定する関数
    引数rct: こうかとんrectまたは爆弾rect
    戻り値:yoko, tate
    画面内:True, 画面外:False
    """
    yoko, tate = True, True
    if rct.left < 0 or WIDTH < rct.right:   # 横方向の画面外判定
        yoko = False
    if rct.top < 0 or HEIGHT < rct.bottom:  # 縦方向の画面外判定
        tate = False
    return yoko, tate

def gameover(screen: pg.Surface):
    """
    ゲームオーバー画面を表示する関数
    画面全体を暗くし、中央に「Game Over」の文字と
    両サイドにこうかとんの画像を表示する。
    5秒間表示した後、関数を終了する。
    """
    overlay: pg.Surface = pg.Surface((WIDTH, HEIGHT))   # 画面全体を覆う透明なサーフェス
    overlay.fill((0, 0, 0))
    overlay.set_alpha(200)

    font: pg.font.Font = pg.font.Font(None, 100)    # フォントオブジェクトの作成
    text_surf: pg.Surface = font.render("Game Over", True, (255, 255, 255))    # "Game Over"の文字を描画したサーフェス
    text_rect: pg.Rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))   # 文字の位置を中央に設定
    overlay.blit(text_surf, text_rect)  # 文字をオーバーレイに描画

    kk_img: pg.Surface = pg.transform.flip(pg.image.load("fig/8.png"), True, False) # こうかとん画像の読み込みと反転
    kk_rect_left: pg.Rect  = kk_img.get_rect(center=(WIDTH // 2 - 240, HEIGHT // 2))    # 左側のこうかとんの位置設定
    kk_rect_right: pg.Rect = kk_img.get_rect(center=(WIDTH // 2 + 240, HEIGHT // 2))    # 右側のこうかとんの位置設定
    overlay.blit(kk_img, kk_rect_left)  # 左側のこうかとんをオーバーレイに描画
    overlay.blit(kk_img, kk_rect_right)  # 右側のこうかとんをオーバーレイに描画
    
    screen.blit(overlay, (0, 0))
    pg.display.update()
    pg.time.wait(5000)


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    時間とともに爆弾が拡大・加速する関数
    戻り値:bb_imgs, bb_accs
    bb_imgs: 拡大した爆弾画像のリスト
    bb_accs: 拡大に伴う加速度のリスト
    1秒ごとに爆弾画像が大きくなり、加速度も増加する。
    それぞれ10段階まで用意する。
    """
    bb_imgs: list[pg.Surface] = []
    for r in range(1, 11):
        bb_img: pg.Surface = pg.Surface((20 * r, 20 * r))   # 爆弾画像の作成
        bb_img.set_colorkey((0, 0, 0))
        bb_img.fill((0, 0, 0))
        pg.draw.circle(bb_img, (255, 0, 0), (10*r, 10*r), 10*r)   # 爆弾の円を描画
        bb_imgs.append(bb_img)

    bb_accs: list[int] = [a for a in range(1, 11)]  # 加速度リストの作成

    return bb_imgs, bb_accs

def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:

    """
    こうかとん画像を辞書型で管理する関数
    戻り値:kk_imgs
    kk_imgs: 方向キーに対応したこうかとん画像の辞書
    """
    kk_dict: dict[tuple[int, int], pg.Surface] = {
        (0, 0): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), True, False), 0, 0.9),       # 立ち止まり
        (5, 0): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), True, False), 0, 0.9),       # 右
        (5, -5): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), True, False), 45, 0.9),    # 右上
        (0,-5): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), False, True), 270, 0.9),     # 上   
        (-5,-5): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), False, False), 315, 0.9),     # 左上
        (-5,0): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), False, False), 0, 0.9),       # 左
        (-5,5): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), False, False), 45, 0.9),     # 左下
        (0,5): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), False, True), 90, 0.9),       # 下
        (5,5): rotozoom(pg.transform.flip(pg.image.load("fig/3.png"), True, False), 315, 0.9),       # 右下
    }

    return kk_dict

def calc_orienration(org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]) -> tuple[float, float]:
    """
    こうかとんに対しての追従型爆弾の移動ベクトルを計算する関数
    引数org: 爆弾rect
    引数dst: こうかとんrect
    引数current_xy: 現在の移動ベクトル
    戻り値: new_xy
    new_xy: 新しい移動ベクトル
    こうかとんの位置に基づいて、爆弾の新しい移動ベクトルを計算する。
    """
    bb_x, bb_y = org.center
    kk_x, kk_y = dst.center
    diff_x: float = kk_x - bb_x
    diff_y: float = kk_y - bb_y
    distance: float = (diff_x ** 2 + diff_y ** 2) ** 0.5    # こうかとんまでの距離

    if distance < 300:  # こうかとんまでの距離が300未満の場合、移動ベクトルを変更しない
        return current_xy

    target_norm: float = (5 ** 2 + 5 ** 2) ** 0.5   # 目標とする移動ベクトルの大きさ
    scale: float = target_norm / distance
    new_vx: float = diff_x * scale
    new_vy: float = diff_y * scale

    return new_vx, new_vy

def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")    
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)

    bb_img = pg.Surface((20, 20))
    pg.draw.circle(bb_img, (255, 0, 0), (10, 10), 10)
    bb_img.set_colorkey((0, 0, 0))

    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    bb_imgs, bb_accs = init_bb_imgs()
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    vx, vy = +5, +5
    clock = pg.time.Clock()
    tmr = 0

    kk_imgs = get_kk_imgs()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
            
        if kk_rct.colliderect(bb_rct):
            print("ゲームオーバー")
            gameover(screen)
            return
        
        screen.blit(bg_img, [0, 0]) 


        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]

        for k, mv in DELTA.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        kk_img = kk_imgs[tuple(sum_mv)]
        kk_rct.move_ip(sum_mv)

        if check_bound(kk_rct) != (True, True):
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])
        screen.blit(kk_img, kk_rct)

        vx, vy = calc_orienration(bb_rct, kk_rct, (vx, vy))
        
        idx = min(tmr // 500, 9)    # 爆弾画像と加速度のインデックスを計算

        bb_img = bb_imgs[idx]   # 現在のインデックスに対応する爆弾画像を取得
        old_center = bb_rct.center  # 爆弾の現在の中心位置を保存
        bb_rct = bb_img.get_rect()  # 新しい爆弾画像のrectを取得
        bb_rct.center = old_center  # 保存した中心位置に設定

        avx = vx * bb_accs[idx] # 加速度を考慮した移動量
        avy = vy * bb_accs[idx] # 加速度を考慮した移動量

        next_rct = bb_rct.copy()
        next_rct.move_ip(avx, avy)

        yoko, tate = check_bound(next_rct)
        if not yoko:
            vx *= -1
            avx *= -1
        if not tate:
            vy *= -1   
            avy *= -1


        bb_rct.move_ip(avx, avy)  # 爆弾の位置を移動
        bb_rct.width = bb_img.get_rect().width
        bb_rct.height = bb_img.get_rect().height

        screen.blit(bg_img, [0, 0])
        screen.blit(bb_img, bb_rct)
        screen.blit(kk_img, kk_rct)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
