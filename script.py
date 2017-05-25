#VARY BUT NO FRAMES DOES NOT WORK

import mdl, os, sys
from display import *
from matrix import *
from draw import *

basename_set = False
basename = 'simple'
frames_set = False
frames = None


"""======== first_pass( commands, symbols ) ==========

  Checks the commands array for any animation commands
  (frames, basename, vary)
  
  Should set num_frames and basename if the frames 
  or basename commands are present

  If vary is found, but frames is not, the entire
  program should exit.

  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.

  jdyrlandweaver
  ==================== """
def first_pass( commands ):
    global frames
    global basename
    global frames_set
    global basename_set

    cmds = [c[0] for c in commands]
    
    if 'vary' in cmds and not 'frames' in cmds:
        print 'Frames was not set before calling vary!'
        sys.exit()

    for command in commands:
        c = command[0]
        args = command[1:]
        
        if c == 'frames':
            frames = args[0]
            frames_set = True
            
        elif c == 'basename':
            basename = args[0]
            basename_set = True

    if frames_set and not basename_set:
        print 'Basename was not set. Basename is now \"simple\"'

    return frames


"""======== second_pass( commands ) ==========

  In order to set the knobs for animation, we need to keep
  a seaprate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).

  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.

  Go through the command array, and when you find vary, go 
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropirate value. 
  ===================="""

knobs = []

def second_pass( commands, num_frames ):
    global knobs
    global frames_set
    
    if not frames_set:
        return

    knobs = [{} for x in range(num_frames)]

    for command in commands:
        c = command[0]
        args = command[1:]

        if c == 'vary':

            name = args[0]
            start_frame  = int(args[1])
            end_frame = int(args[2])
            start_val = float(args[3])
            end_val = float(args[4])

            diff_frame = end_frame - start_frame

            if diff_frame < 0 or start_frame < 0 or end_frame >= frames:
                print 'Invalid frame range specified'
                return

            diff_val = end_val - start_val
            change_diff = diff_val / diff_frame
            inc = start_val
            m = 1
            
            if change_diff < 0:
                temp = start_frame
                start_frame = end_frame
                end_frame = temp
                change_diff *= -1.0 #make it positive
                m *= -1 #go backwards in frames
                inc = end_val #change the start
                end_val = start_val  #change the end
                
            for i in range(start_frame,end_frame+m,m):
                knobs[i][name] = inc
                
                if inc < end_val:
                    inc += change_diff
                    
                    
    return knobs
                
def run(filename):
    """
    This function runs an mdl script
    """
    global frames
    global frames_set
    global basename
    global basename_set
    global knobs
    
    color = [255, 255, 255]
    tmp = new_matrix()
    ident( tmp )
    screen = new_screen()
    step = 0.01
    
    p = mdl.parseFile(filename)

    if p:
        (commands, symbols) = p
    else:
        print "Parsing failed."
        return

    first_pass(commands)
    second_pass(commands,frames)

    if not frames_set:
        frames = 1
    
    for i in range(frames):
        tmp = new_matrix()
        ident(tmp)
        stack = [ [x[:] for x in tmp] ]
        
        tmp = []
        step = 0.1
        for command in commands:
            print command
            c = command[0]
            args = command[1:]

            if c == 'set':
                symbols[args[0]][1] = float(args[1]) 

            elif c == 'setknobs':
                for s in symbols:
                    if symbols[s][0] == 'knob':
                        symbols[s][1] = float(args[0])

            elif c == 'color':
                color[:] = [args[0],args[1],args[2]]
                
            elif c == 'box':
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, color)
                tmp = []
            elif c == 'sphere':
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, color)
                tmp = []
            elif c == 'torus':
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, color)
                tmp = []
            elif c == 'move':
                
                if args[3] != None:
                    a = knobs[i][args[3]] * args[0]
                    b = knobs[i][args[3]] * args[1]
                    c = knobs[i][args[3]] * args[2]
                    args = (a,b,c,args[3])
                
                tmp = make_translate(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                
                if args[3] != None:
                    a = knobs[i][args[3]] * args[0]
                    b = knobs[i][args[3]] * args[1]
                    c = knobs[i][args[3]] * args[2]
                    args = (a,b,c,args[3])
                
                tmp = make_scale(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':

                if args[2] != None:
                    a = knobs[i][args[2]] * args[1]
                    args = (args[0],a,args[2])
                
                theta = args[1] * (math.pi/180)
                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []
                
            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                display(screen)
            elif c == 'save':
                save_extension(screen, args[0])

        name = 'anim/' + basename + (3-len(str(i)))*'0' + str(i) + '.ppm'

        if not os.path.exists('anim'):
            os.makedirs('anim')
        
        save_ppm(screen,name)
        clear_screen(screen)

    make_animation(basename)
    print symbols
