import axi
import time

def pen_up(device):
    device.command('SC', 10, 0)
    device.command('SP', 0, 200)

def pen_z_to(device, to_z, ms):
    dz = abs(to_z - device.pen_z)
    s = dz / (0.0 +  ms)
    r = s * 24.0

    print('dz : %d ms : %d s : %d r : %d' % (dz, ms, s, r))

    r = int(r)

    device.command('SC', 10, r)
    device.command('SC', 4, to_z)
    device.command('SP', 1, 0)

    device.pen_z = to_z

def move_to(device, to_x, to_y, to_z, ms):
    if to_x < X_Range[0]: to_x = X_Range[0]
    if to_x > X_Range[1]: to_x = X_Range[1]
    if to_y < Y_Range[0]: to_y = Y_Range[0]
    if to_y > Y_Range[1]: to_y = Y_Range[1]
    if to_z < Z_Range[0]: to_z = Z_Range[0]
    if to_z > Z_Range[1]: to_z = Z_Range[1]

    print('move to x : %d y : %d z : %d ms : %d' % (to_x, to_y, to_z, ms))
    print('cur pos x : %d y : %d z : %d' % (device.pen_x, device.pen_y, device.pen_z))

    dx = to_x - device.pen_x
    dy = to_y - device.pen_y

    print('dx : %d dy : %d' % (dx, dy))

    pen_z_to(device, to_z, ms)

    device.stepper_move(int(ms), int(dx), int(dy))

    device.pen_x = to_x
    device.pen_y = to_y

    time.sleep(ms/1000)


# servo levels ("min"/"max")
# - SC,5,Z (up) or SC,4,Z (dn)
# - Z in [1,65535] (for Axidraw [7500,28000])
# - controls a pulse width in ns for a servo controller
# - units of 83ns of duty cycle (units of 1/12000th of a second)
#   - e.g. 16000 * 83ns = 1.33ms
# - wider pulse makes the pen go higher in z
# - pulses are sent out each 24ms
#
# servo rate SC,10,R
# - if R=0 then SC,5 takes effect immediately 
#   - new pulse width starts coming out immediately after cmd executes
#   - I guess this means hardware goes as fast as it can
# - if R != 0 then when you issue SC,5
#   - first the hardware outputs the old rate
#   - then every 24ms
#     - the system adds/subtracts R to to get towards the new rate
#     - until enough 24ms periods happened to get to new rate
#   - so R    = height unit change per 24ms
#   - so if we have desired speed S = height unit change per ms
#        R = S*24

# X,Y 1000 = 0.5 inch = 12.7 mm
# X range [0, 23385]
# Y range [0, 17000]

X_Range = [0, 23385]
Y_Range = [0, 17000]
# Z_Range = [6000, 28000]
Z_Range = [17000, 28000]

# draw_Z_Range = [17000, 18500]
draw_Z_Range = [17000, 17700]
no_draw_Z = 20000

def main(fonts_pts_list):
    device = axi.Device()

    device.pen_x,device.pen_y = device.read_position()

    # reset
    device.command('R')

    # set pen up pos nice and high
    # pen up pos, default 16000, more higher
    device.command('SC', 5, 20000)
    # quickly put pen in known down pos
    # servo rate ("quick as possible")
    device.command('SC', 10, 0)
    device.pen_z = 20000
    # pen down pos, default 12000, more higher
    device.command('SC', 4, device.pen_z)
    # pen down (200ms enough for "quick as possible")
    device.command('SP', 1, 200)

    pen_up(device)

    font_span = 1000
    base_pt = [5000, 2000]
    scale_x = 3
    scale_y = 3
    for pts_list in fonts_pts_list:
        # find min max Z value
        min_z = None
        max_z = None
        for pts in pts_list:
            for pt in pts:
                if min_z is None or min_z > pt[2]:
                    min_z = pt[2]
                if max_z is None or max_z < pt[2]:
                    max_z = pt[2]
        
        # normalize pt
        for i,pts in enumerate(pts_list):
            for j,pt in enumerate(pts):
                pts_list[i][j][0] = pts_list[i][j][0] * scale_x
                pts_list[i][j][1] = pts_list[i][j][1] * scale_y
                pts_list[i][j][2] = ((draw_Z_Range[1] - draw_Z_Range[0]) / (max_z - min_z)) * (pts_list[i][j][2] - min_z) + draw_Z_Range[0]

        move_to(device, base_pt[0] + pts_list[0][0][1], base_pt[1] + pts_list[0][0][0], no_draw_Z, 2000)
        for i,pts in enumerate(pts_list):
            move_to(device, base_pt[0] + pts[0][1], base_pt[1] + pts[0][0], no_draw_Z, 500)
            for pt in pts:
                move_to(device, base_pt[0] + pt[1], base_pt[1] + pt[0], pt[2], 200)
            move_to(device, base_pt[0] + pts[-1][1], base_pt[1] + pts[-1][0], no_draw_Z, 300)
            # time.sleep(1)

        base_pt[1] += font_span

    # time.sleep(2)

    # move_to(device, 5000, 2000, 12000, 2000)
    # # move_to(device, 5000, 5000, 6000, 2000)

    # time.sleep(2)
    
    # move_to(device, 7000, 2000, 14000, 4000)
    # # move_to(device, 23385, 17000, 10000, 3000)
    # # move_to(device, 4000, 2000, 9000, 1200)

    pen_up(device)
    move_to(device, 0, 0, 20000, 2000)


if __name__ == '__main__':
    # fonts_pts_list = [[[[61, 66, 16], [86, 65, 16], [108, 64, 16], [128, 62, 16], [145, 60, 16], [160, 57, 16], [171, 54, 16], [181, 50, 16], [187, 45, 16], [191, 40, 16]], [[146, 162, 15], [156, 161, 14], [165, 159, 14], [174, 156, 13], [181, 153, 13], [187, 148, 13], [192, 141, 12], [196, 134, 12], [198, 126, 11], [200, 116, 11]], [[62, 75, 18], [66, 74, 18], [71, 73, 19], [74, 71, 19], [78, 69, 20], [80, 66, 21], [83, 62, 21], [84, 57, 22], [86, 52, 22], [86, 47, 23]], [[133, 155, 10], [134, 135, 10], [137, 117, 10], [141, 100, 10], [146, 86, 11], [152, 73, 11], [158, 61, 11], [166, 52, 12], [174, 44, 12], [184, 38, 12]], [[63, 166, 6], [64, 180, 6], [67, 193, 7], [70, 205, 8], [74, 215, 8], [80, 223, 9], [86, 230, 10], [92, 236, 10], [100, 239, 11], [109, 242, 12]]], [[[39, 52, 11], [69, 51, 12], [95, 50, 13], [119, 48, 14], [140, 45, 15], [157, 42, 16], [171, 38, 17], [182, 33, 18], [190, 27, 19], [195, 21, 20]], [[163, 160, 16], [174, 159, 15], [184, 157, 15], [194, 154, 15], [202, 149, 14], [208, 143, 14], [214, 136, 14], [218, 128, 13], [221, 118, 13], [223, 107, 13]], [[128, 146, 8], [128, 128, 9], [130, 112, 10], [134, 96, 11], [139, 82, 12], [145, 69, 13], [152, 57, 14], [161, 46, 15], [172, 36, 16], [183, 27, 17]], [[34, 198, 8], [35, 203, 9], [37, 208, 11], [39, 213, 13], [42, 217, 14], [45, 221, 16], [48, 223, 18], [52, 226, 19], [56, 228, 21], [61, 229, 23]], [[63, 72, 15], [66, 67, 15], [70, 62, 15], [73, 58, 15], [75, 53, 15], [78, 48, 16], [80, 44, 16], [82, 39, 16], [83, 34, 16], [85, 29, 16]]], [[[54, 71, 12], [73, 71, 16], [91, 72, 20], [107, 74, 24], [120, 76, 28], [132, 78, 32], [141, 81, 36], [148, 85, 40], [153, 88, 44], [156, 93, 48]], [[72, 151, 9], [73, 166, 9], [77, 180, 10], [83, 193, 10], [91, 204, 11], [101, 215, 12], [112, 223, 12], [126, 231, 13], [141, 238, 13], [158, 243, 14]], [[147, 117, 37], [148, 108, 35], [150, 99, 33], [152, 90, 31], [155, 81, 29], [157, 72, 27], [160, 64, 25], [163, 55, 23], [166, 46, 21], [170, 38, 19]]], [[[64, 78, 16], [85, 78, 17], [104, 78, 19], [121, 79, 21], [136, 81, 23], [148, 83, 25], [158, 85, 26], [166, 88, 28], [172, 92, 30], [175, 95, 32]], [[169, 77, 28], [169, 69, 27], [169, 61, 26], [169, 55, 25], [169, 49, 24], [170, 44, 24], [171, 39, 23], [171, 35, 22], [172, 32, 21], [173, 29, 20]], [[110, 195, 4], [115, 201, 6], [121, 208, 8], [126, 213, 10], [131, 218, 12], [137, 223, 14], [141, 226, 16], [146, 229, 18], [151, 232, 20], [155, 233, 22]], [[95, 105, 16], [95, 104, 15], [95, 101, 15], [95, 97, 15], [95, 91, 15], [95, 84, 15], [95, 75, 15], [95, 64, 15], [95, 52, 15], [95, 38, 15]]], [[[70, 77, 17], [71, 76, 16], [74, 75, 15], [80, 75, 14], [89, 75, 14], [100, 74, 13], [113, 74, 12], [129, 74, 12], [148, 74, 11], [168, 74, 10]], [[94, 206, 6], [97, 211, 6], [100, 217, 7], [104, 222, 8], [108, 227, 9], [113, 231, 10], [118, 234, 10], [124, 238, 11], [130, 240, 12], [137, 243, 13]], [[176, 29, 9], [176, 44, 10], [176, 58, 12], [176, 70, 14], [176, 81, 15], [177, 90, 17], [177, 97, 19], [178, 103, 20], [179, 107, 22], [180, 110, 24]], [[97, 101, 11], [97, 94, 10], [98, 87, 10], [99, 80, 9], [100, 72, 9], [101, 64, 9], [101, 56, 8], [102, 47, 8], [102, 37, 7], [102, 28, 7]]], [[[116, 247, 14], [126, 245, 14], [136, 241, 14], [146, 235, 14], [156, 226, 14], [166, 215, 14], [175, 201, 14], [184, 184, 14], [193, 165, 14], [201, 144, 14]], [[25, 60, 10], [26, 65, 10], [30, 71, 10], [37, 75, 10], [48, 79, 11], [61, 83, 11], [76, 86, 11], [95, 88, 12], [117, 89, 12], [141, 90, 12]], [[150, 142, 16], [150, 133, 15], [151, 124, 15], [154, 115, 15], [157, 106, 14], [161, 97, 14], [166, 87, 14], [173, 77, 13], [180, 67, 13], [188, 57, 13]], [[80, 164, 8], [81, 178, 8], [84, 191, 9], [87, 202, 10], [92, 212, 10], [97, 220, 11], [103, 227, 12], [110, 233, 12], [118, 237, 13], [127, 239, 14]], [[80, 116, 15], [81, 111, 14], [82, 105, 14], [83, 98, 13], [84, 90, 13], [85, 81, 12], [85, 70, 12], [86, 58, 11], [86, 45, 11], [86, 30, 10]], [[167, 148, 19], [172, 147, 17], [178, 144, 16], [182, 140, 15], [186, 134, 13], [190, 126, 12], [193, 116, 11], [195, 105, 9], [196, 92, 8], [197, 77, 7]], [[139, 249, 12], [144, 242, 11], [150, 234, 11], [157, 223, 10], [166, 210, 10], [176, 195, 9], [187, 178, 9], [199, 158, 8], [213, 137, 8], [228, 113, 7]]], [[[52, 70, 15], [80, 69, 15], [106, 68, 16], [128, 65, 16], [148, 62, 17], [164, 57, 18], [178, 52, 18], [188, 45, 19], [196, 38, 19], [200, 30, 20]], [[175, 122, 16], [182, 121, 14], [189, 118, 13], [195, 114, 12], [201, 108, 11], [205, 101, 10], [209, 91, 9], [212, 80, 8], [214, 68, 7], [215, 53, 6]], [[96, 85, 16], [100, 81, 15], [104, 76, 15], [107, 71, 15], [110, 66, 15], [113, 60, 15], [115, 53, 14], [117, 46, 14], [119, 38, 14], [120, 29, 14]], [[107, 212, 7], [110, 216, 7], [115, 221, 8], [119, 225, 9], [124, 229, 9], [129, 232, 10], [134, 236, 11], [139, 239, 11], [145, 242, 12], [151, 244, 13]], [[162, 117, 13], [162, 107, 13], [164, 98, 13], [166, 89, 13], [169, 79, 13], [173, 69, 13], [177, 59, 13], [183, 49, 13], [189, 39, 13], [196, 28, 13]], [[52, 59, 16], [53, 61, 15], [57, 64, 14], [64, 66, 13], [75, 67, 12], [88, 69, 12], [103, 70, 11], [122, 71, 10], [144, 72, 9], [168, 72, 8]]], [[[57, 56, 18], [68, 57, 17], [80, 58, 16], [92, 60, 15], [104, 61, 14], [116, 62, 13], [128, 63, 12], [141, 63, 11], [153, 64, 10], [166, 64, 9]], [[74, 248, 11], [83, 246, 11], [94, 242, 11], [105, 235, 11], [117, 226, 11], [130, 214, 11], [143, 200, 11], [157, 182, 11], [172, 163, 11], [187, 140, 11]], [[113, 149, 8], [114, 136, 8], [117, 123, 9], [122, 111, 9], [128, 99, 10], [137, 87, 10], [147, 75, 11], [158, 64, 11], [172, 53, 12], [187, 42, 12]], [[114, 128, 6], [114, 135, 7], [115, 142, 8], [118, 148, 9], [120, 153, 10], [124, 158, 11], [128, 161, 12], [134, 164, 13], [139, 166, 14], [146, 167, 15]], [[61, 57, 15], [69, 56, 14], [77, 55, 14], [83, 54, 13], [89, 52, 13], [94, 50, 13], [98, 46, 12], [101, 43, 12], [104, 39, 11], [105, 34, 11]]], [[[77, 71, 17], [93, 72, 20], [108, 73, 24], [121, 75, 27], [133, 76, 31], [143, 78, 35], [150, 80, 38], [157, 81, 42], [161, 83, 45], [164, 85, 49]], [[55, 175, 10], [57, 183, 10], [61, 191, 11], [67, 198, 12], [73, 205, 13], [81, 212, 14], [90, 218, 14], [100, 224, 15], [112, 229, 16], [125, 234, 17]]], [[[51, 72, 12], [72, 72, 15], [92, 72, 19], [109, 72, 23], [124, 73, 27], [137, 74, 31], [147, 75, 35], [155, 76, 39], [161, 78, 43], [164, 80, 47]], [[173, 242, 27], [174, 236, 24], [176, 230, 22], [178, 223, 20], [181, 214, 18], [185, 204, 16], [190, 193, 13], [195, 181, 11], [201, 167, 9], [208, 152, 7]], [[73, 82, 17], [90, 81, 20], [106, 81, 23], [120, 81, 26], [132, 81, 30], [143, 80, 33], [151, 80, 36], [158, 80, 40], [162, 79, 43], [165, 79, 46]]], [[[75, 43, 25], [96, 42, 23], [116, 42, 22], [133, 42, 20], [149, 41, 19], [163, 41, 18], [175, 40, 16], [185, 39, 15], [194, 38, 13], [200, 37, 12]], [[129, 133, 14], [130, 121, 14], [134, 110, 14], [138, 100, 14], [144, 89, 14], [151, 79, 14], [159, 69, 14], [169, 59, 14], [180, 49, 14], [192, 39, 14]], [[158, 162, 14], [172, 161, 13], [184, 159, 12], [195, 156, 11], [205, 152, 11], [213, 146, 10], [220, 140, 9], [225, 132, 9], [229, 122, 8], [231, 112, 7]], [[84, 26, 20], [93, 28, 18], [104, 32, 17], [116, 37, 16], [129, 43, 15], [144, 51, 14], [159, 60, 12], [176, 71, 11], [195, 83, 10], [215, 96, 9]], [[29, 174, 11], [29, 184, 11], [30, 194, 11], [33, 203, 11], [36, 211, 11], [41, 218, 12], [46, 224, 12], [52, 229, 12], [59, 234, 12], [67, 237, 12]]], [[[36, 75, 7], [46, 75, 8], [58, 75, 9], [72, 76, 10], [87, 76, 12], [104, 76, 13], [122, 76, 14], [142, 76, 16], [164, 76, 17], [188, 76, 18]], [[169, 170, 21], [177, 169, 19], [185, 166, 18], [192, 161, 17], [198, 155, 16], [204, 147, 15], [209, 137, 13], [213, 125, 12], [217, 112, 11], [219, 97, 10]], [[141, 154, 9], [141, 143, 9], [143, 132, 10], [146, 121, 10], [150, 109, 11], [155, 97, 12], [161, 84, 12], [168, 71, 13], [177, 57, 13], [187, 42, 14]]], [[[43, 75, 15], [63, 74, 15], [82, 73, 16], [99, 70, 17], [116, 67, 17], [131, 63, 18], [144, 58, 19], [157, 52, 19], [168, 45, 20], [177, 37, 21]], [[157, 144, 15], [168, 143, 15], [179, 140, 15], [189, 135, 15], [197, 129, 15], [204, 121, 16], [209, 111, 16], [214, 99, 16], [217, 86, 16], [219, 71, 16]], [[75, 186, 9], [77, 192, 9], [79, 199, 10], [83, 205, 11], [87, 211, 12], [92, 218, 13], [98, 224, 14], [104, 230, 15], [111, 236, 16], [118, 242, 17]], [[129, 124, 13], [131, 109, 13], [134, 95, 14], [138, 82, 15], [142, 71, 15], [148, 62, 16], [154, 53, 17], [161, 46, 17], [169, 40, 18], [178, 35, 19]], [[69, 86, 16], [82, 81, 16], [96, 77, 16], [109, 72, 16], [121, 67, 16], [133, 62, 17], [145, 56, 17], [156, 50, 17], [167, 44, 17], [177, 37, 17]]]]
    # fonts_pts_list = [[[[61, 66, 16], [86, 65, 16], [108, 64, 16], [128, 62, 16], [145, 60, 16], [160, 57, 16], [171, 54, 16], [181, 50, 16], [187, 45, 16], [191, 40, 16]], [[146, 162, 15], [156, 161, 14], [165, 159, 14], [174, 156, 13], [181, 153, 13], [187, 148, 13], [192, 141, 12], [196, 134, 12], [198, 126, 11], [200, 116, 11]], [[62, 75, 18], [66, 74, 18], [71, 73, 19], [74, 71, 19], [78, 69, 20], [80, 66, 21], [83, 62, 21], [84, 57, 22], [86, 52, 22], [86, 47, 23]], [[133, 155, 10], [134, 135, 10], [137, 117, 10], [141, 100, 10], [146, 86, 11], [152, 73, 11], [158, 61, 11], [166, 52, 12], [174, 44, 12], [184, 38, 12]], [[63, 166, 6], [64, 180, 6], [67, 193, 7], [70, 205, 8], [74, 215, 8], [80, 223, 9], [86, 230, 10], [92, 236, 10], [100, 239, 11], [109, 242, 12]]], [[[39, 52, 11], [69, 51, 12], [95, 50, 13], [119, 48, 14], [140, 45, 15], [157, 42, 16], [171, 38, 17], [182, 33, 18], [190, 27, 19], [195, 21, 20]], [[163, 160, 16], [174, 159, 15], [184, 157, 15], [194, 154, 15], [202, 149, 14], [208, 143, 14], [214, 136, 14], [218, 128, 13], [221, 118, 13], [223, 107, 13]], [[128, 146, 8], [128, 128, 9], [130, 112, 10], [134, 96, 11], [139, 82, 12], [145, 69, 13], [152, 57, 14], [161, 46, 15], [172, 36, 16], [183, 27, 17]], [[34, 198, 8], [35, 203, 9], [37, 208, 11], [39, 213, 13], [42, 217, 14], [45, 221, 16], [48, 223, 18], [52, 226, 19], [56, 228, 21], [61, 229, 23]], [[63, 72, 15], [66, 67, 15], [70, 62, 15], [73, 58, 15], [75, 53, 15], [78, 48, 16], [80, 44, 16], [82, 39, 16], [83, 34, 16], [85, 29, 16]]], [[[54, 71, 12], [73, 71, 16], [91, 72, 20], [107, 74, 24], [120, 76, 28], [132, 78, 32], [141, 81, 36], [148, 85, 40], [153, 88, 44], [156, 93, 48]], [[72, 151, 9], [73, 166, 9], [77, 180, 10], [83, 193, 10], [91, 204, 11], [101, 215, 12], [112, 223, 12], [126, 231, 13], [141, 238, 13], [158, 243, 14]], [[147, 117, 37], [148, 108, 35], [150, 99, 33], [152, 90, 31], [155, 81, 29], [157, 72, 27], [160, 64, 25], [163, 55, 23], [166, 46, 21], [170, 38, 19]]]]
    fonts_pts_list = [[[[45, 149, 21], [58, 149, 19], [72, 149, 18], [89, 149, 16], [106, 149, 15], [126, 149, 14], [147, 149, 12], [169, 149, 11], [193, 149, 9], [218, 149, 8]], [[24, 60, 14], [47, 58, 14], [69, 56, 15], [88, 54, 16], [104, 52, 16], [119, 49, 17], [131, 46, 18], [140, 43, 18], [147, 40, 19], [152, 36, 20]], [[107, 224, 10], [107, 203, 10], [109, 182, 10], [112, 162, 11], [115, 142, 11], [120, 123, 12], [126, 104, 12], [132, 85, 12], [140, 66, 13], [149, 48, 13]], [[21, 48, 14], [27, 48, 15], [32, 49, 16], [37, 51, 17], [42, 54, 19], [45, 57, 20], [48, 61, 21], [51, 65, 23], [52, 70, 24], [53, 76, 25]], [[125, 225, 16], [134, 224, 15], [142, 223, 14], [149, 222, 13], [156, 220, 12], [161, 217, 12], [166, 214, 11], [169, 210, 10], [172, 205, 9], [173, 200, 8]], [[52, 147, 21], [67, 146, 19], [83, 146, 17], [100, 145, 15], [119, 145, 13], [139, 144, 11], [159, 144, 8], [181, 143, 6], [204, 142, 4], [228, 141, 2]], [[54, 144, 20], [76, 144, 18], [96, 145, 17], [113, 146, 16], [129, 149, 15], [142, 152, 14], [152, 155, 12], [160, 159, 11], [166, 164, 10], [170, 169, 9]]], [[[8, 142, 11], [17, 136, 10], [27, 130, 10], [38, 125, 10], [48, 120, 10], [60, 116, 10], [71, 112, 10], [84, 109, 10], [96, 106, 10], [109, 104, 10]], [[96, 109, 9], [97, 118, 9], [101, 127, 9], [108, 135, 9], [117, 141, 9], [129, 147, 9], [144, 151, 9], [162, 155, 9], [182, 157, 9], [205, 159, 9]], [[117, 156, 5], [140, 155, 5], [162, 155, 5], [181, 155, 5], [198, 155, 5], [213, 154, 5], [225, 153, 5], [235, 153, 5], [243, 152, 5], [249, 151, 5]]], [[[3, 117, 9], [22, 125, 9], [41, 132, 9], [59, 139, 9], [76, 146, 9], [93, 153, 10], [110, 159, 10], [125, 164, 10], [141, 169, 10], [155, 174, 10]], [[195, 71, 4], [202, 72, 4], [208, 74, 5], [214, 77, 6], [220, 82, 7], [225, 87, 8], [229, 94, 8], [233, 102, 9], [236, 111, 10], [239, 120, 11]], [[100, 163, 13], [103, 162, 12], [106, 160, 12], [109, 156, 11], [112, 151, 11], [114, 145, 10], [115, 138, 10], [117, 129, 9], [118, 118, 9], [118, 107, 8]], [[58, 149, 12], [60, 148, 11], [63, 146, 10], [65, 143, 10], [66, 138, 9], [68, 133, 9], [69, 126, 8], [70, 118, 7], [71, 108, 7], [71, 97, 6]], [[168, 180, 6], [168, 164, 5], [168, 149, 5], [169, 136, 5], [170, 123, 4], [172, 113, 4], [173, 103, 4], [175, 95, 3], [178, 88, 3], [180, 83, 3]]], [[[78, 56, 11], [80, 75, 10], [84, 92, 10], [90, 107, 10], [98, 120, 10], [107, 132, 10], [118, 141, 10], [131, 148, 10], [146, 153, 10], [162, 156, 10]], [[34, 94, 14], [40, 93, 13], [47, 91, 13], [53, 89, 13], [60, 85, 12], [66, 80, 12], [71, 74, 12], [77, 67, 11], [82, 59, 11], [87, 50, 11]], [[150, 158, 9], [165, 157, 8], [179, 154, 8], [192, 150, 8], [203, 145, 8], [212, 138, 8], [220, 130, 8], [226, 120, 8], [230, 109, 8], [232, 97, 8]], [[179, 213, 12], [187, 212, 11], [195, 211, 11], [203, 210, 10], [210, 207, 10], [218, 204, 9], [226, 201, 9], [233, 196, 8], [240, 191, 8], [247, 186, 7]], [[160, 161, 9], [164, 147, 8], [169, 134, 8], [175, 123, 8], [183, 114, 8], [191, 106, 8], [201, 99, 7], [211, 94, 7], [223, 90, 7], [236, 88, 7]]], [[[39, 176, 3], [54, 151, 4], [70, 128, 5], [86, 107, 7], [103, 88, 8], [119, 72, 10], [135, 57, 11], [152, 44, 12], [169, 34, 14], [186, 25, 15]], [[89, 239, 20], [103, 238, 18], [117, 236, 17], [131, 233, 16], [145, 230, 15], [158, 225, 14], [170, 218, 12], [182, 211, 11], [194, 203, 10], [206, 193, 9]], [[112, 51, 23], [117, 50, 21], [124, 48, 20], [132, 46, 18], [140, 44, 17], [150, 40, 15], [160, 36, 13], [171, 32, 12], [184, 26, 11], [197, 20, 9]], [[47, 162, 10], [47, 176, 10], [49, 190, 10], [53, 201, 11], [58, 211, 11], [64, 220, 12], [72, 227, 12], [81, 232, 12], [92, 236, 13], [104, 239, 13]]], [[[50, 242, 15], [59, 216, 14], [69, 194, 14], [80, 174, 14], [91, 157, 14], [104, 142, 14], [117, 130, 13], [131, 121, 13], [146, 114, 13], [162, 110, 13]], [[129, 110, 2], [145, 111, 3], [160, 113, 5], [173, 116, 7], [185, 120, 8], [195, 125, 10], [203, 130, 12], [209, 137, 13], [214, 145, 15], [217, 154, 17]], [[66, 22, 9], [69, 41, 9], [73, 59, 9], [78, 75, 9], [83, 89, 10], [90, 100, 10], [98, 110, 10], [107, 117, 11], [116, 122, 11], [127, 125, 11]]]]


    main(fonts_pts_list)