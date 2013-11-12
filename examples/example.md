---
lesson: Lesson X
lesson_title: Example Lesson
language: en
...

# Introduction { .intro}

This term we're going to be learning a computer programming language called Python. The person who created Python named it after his favourite TV show: Monty Python’s Flying Circus. Python is used by loads of programmers for many different things.  Python is a powerful and clever language, used at YouTube, NASA, CERN and others. If your club has a Raspberry Pi, you can use Python to program it. Many people love Python because it is easy to read (at least compared to some other programming languages). Being able to read code is a very important skill, just as important as writing it.


# Hello, Turtle! {.activity}

## Activity Checklist {.check}

Next, we're going to have some fun with turtles. A turtle is a tiny robot that draws on your screen, we can tell it to move around using Python commands.

+ Open a new code window (From the File menu) and write the following:  

    ```python
    from turtle import *
    
    forward(100)
     
    ```
+ Save your program as myturtle.py and choose Run -> Run Module. See how the turtle moved forward 100 pixels? The turtle has a pen attached, and draws lines as it moves around the screen.  

    __ProTip:__ Python program files should always be given a name ending in '.py'.

+ Let's make the turtle move around the canvas! Try using `backward(distance)` as well as turning the turtle by using `right(angle)` and `left(angle)`. Eg `backward(20)` tells the turtle to move backwards 20 pixels, and `right(90)` tells the turtle to turn right 90 degrees. You can give more than one instruction at a time, they will be executed in order.

    ```python
    from turtle import *
    
    speed(11)
    shape("turtle")
    
    forward(100)
    right(120)
    forward(100)
    left(90)
    backward(100)
    left(90)
    forward(50)
     
    ```

## Angles and Degrees

Play around a bit writing your own shapes, using `forward`, `backward`, `left`, `right`. Remember, `forward` and `backward` move in pixels, but `left` and `right` turn in angles. Let's look at a turtle turning right.

```
        North
          0
          |
West      |     East
 270 -----+----- 90
          |
          |
         180
        South
```

When the turtle is facing North, turning right 90 degrees, makes it face East, turning 180 degrees makes it face south, and turning 270 degrees makes it face West. If you turn 360 degrees, you end up where you started.

What about turning left?

```
        North
          0
          |
West      |     East
  90 -----+----- 270
          |
          |
         180
        South
```

When the turtle is facing North, turning left 90 degrees, makes it face West, turning 180 degrees makes it face south, and turning 270 degrees makes it face East. If you turn 360 degrees, you end up where you started. One full turn is always 360 degrees.


##What does the code at the beginning of our program do

* `from turtle import *` tells Python we want to use the turtle library, a collection of code we can use to draw on the screen. Using a library means we can save time.

* `speed()` sets the speed of the turtle, it takes a value between 1 and 11. 11 is the fastest, 1 is the slowest. 
* `shape()` We are using the "turtle" shape, but it can also take the values "arrow", "circle", "square", "triangle" or "classic".

We will be putting these three instructions at the top of all our programs in this lesson. If you like you can make your turtle a different shape, or go as fast or slow as you want.


#**Step4:**  Herbert turns into a ghost when he’s caught {.activity}

##Activity Checklist { .check}

Instead of Felix saying something, we want Herbert to turn into a ghost when he’s caught.

+ Change Felix’s script to send this message when he catches Herbert:

```scratch
				when FLAG clicked
				forever
					point towards [mouse-pointer v]
					move (10) steps
					next costume
					play drum [62 v] for (0.3) beats
					if <touching [herbert v]?>
						broadcast [caught v]
						play drum [58 v] for (0.2) beats
						wait (1) secs
					end
				end

```

+ Import a new costume into Herbert from fantasy/ghost2-a.
+ Edit the costume to make it smaller. Six clicks on the shrink button should do.
+ Change the names of Herbert’s costumes so the mouse costume is called ‘alive’ and the ghost costume is called ‘dead’.
+ Create a new script for Herbert to turn him into a ghost:

```scratch
	when I receive [caught v]
		switch to costume [dead v]
		wait (1) secs
		switch to costume [alive v]

```

##Test your project { .flag}

+ Does Herbert turn into a ghost when he’s caught? 
+ Does Felix play the right sounds at the right time? 			
+ Does Felix still stay still for long enough for Herbert to get away? 


##Save your project { .save}
