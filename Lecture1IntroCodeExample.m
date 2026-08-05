disp("==================")
disp("Intro to Matlab")
disp("Pouya Borjian")
disp(datetime("today"))
disp("==================")
% this is a comment, it will not be executed
% assign variables
x = 2; % what id we do not want to print this lane?
disp(x)
% define an array
x = [1, 2, 3];
% or you can leave out the commas
y = [1 2 3];
% Row vectors and column vectors (matrix)
z = [1; 2; 3];
z2 = [1,2,3;4,5,6;7,8,9;];
% to access a particular element in the array/vector
disp(z(1)) %should print "1" here
disp(z2(3,3)) %should print "9" here
x2 = 1:5;
disp(x2)
x3 = 1:0.25:2;
disp(x3)
z2(:,2) % extract column 2 only, so it should print 2,5,8
z2(:,3)
z2(1:2,2) %first row and second row, second column only, so it should print 2,5
% basic operations
a = 36;
b = 25;
c = 10;
ans1 = a + b
ans2 = a * b
ans3 = (a + c) / b
% dot product
x = [1;2;3]
y = [4;5;6]
%w = x * y
%w2 = y * x
% the above won't work becasue in formal mathemtics the dot product is a
% row vector into a column vector, not other way around
w = dot(x,y)
w2 = dot(y,x) % will we get the same answer?
% use clc to clear command window
% dynamically addint elements to an array
array = [1,2];
disp(array)
array(3) = 3;
disp(array)
% loops
end_of_loop = 5;
for i = 1:end_of_loop
disp("lalala")
end
i = 1;
while i < end_of_loop
disp("lalala")
i = i + 1; % you cannot use i++ in Matlab
end
% conditional statement
if a > b
disp("ha")
elseif a < b
disp("da")
else
disp("pa")
end
% test using your data
quizzes = [60,80,70,90,100,100,40,90];
projects = [96,85,90,100,48,100,80,89,100];
exam1 = 89;
exam2 = 68;
% I want an 80
target = 80;
what_do_i_need_on_my_final(target, quizzes, projects, exam1, exam2)
final = 79;
% plot
t = 0:0.1:5;
f = cos(t*pi/8);
plot(t, f);
title("The first plot");
xlabel("t");
ylabel("f");
% In Matlab, functions must be at the end of the file if they are in the
% same file
[percent, letter] = wHaTisMygRAdE(quizzes, projects, exam1, exam2, final);
fprintf("My grade is %.4f (%s)\n", percent, letter)
function [percent, letter] = wHaTisMygRAdE(quizzes,projects,exam1,exam2,final)
percent = 0.2*mean(quizzes) + 0.3*mean(projects) + ...
0.15*exam1 + 0.15*exam2 + 0.2*final;
if percent >= 90
letter = "A";
elseif percent >= 88
letter = "A-";
elseif percent >= 86
letter = "B+";
elseif percent >= 80
letter = "B";
elseif percent >= 78
letter = "B-";
elseif percent >= 76
letter = "C+";
elseif percent >= 70
letter = "C";
else
letter = "RIP";
end
end
function what_do_i_need_on_my_final(target, quizzes, projects, exam1, exam2)
current = 0.2*mean(quizzes) + 0.3*mean(projects) + ...
0.15*exam1 + 0.15*exam2;
gradeneeded = (target-current)/0.2;
if gradeneeded > 100
fprintf("I need a %.3f on the final.\n", gradeneeded)
fprintf("RIP\n\n")
elseif gradeneeded < 0
fprintf("I need a %.3f on the final.\n", gradeneeded)
fprintf("that means you I am above my target...\n\n")
else
fprintf("I need a %.3f on the final.\n\n", gradeneeded)
end
end