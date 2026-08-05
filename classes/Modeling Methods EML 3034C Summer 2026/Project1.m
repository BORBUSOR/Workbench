% Clear command window, close all graphs, clear workspace
clc; clear; close all;
% ========================================================================
fprintf("============================================================\n")
fprintf("Project 1 - Round-off vs Truncation Error\n")
fprintf("Sebastian Rivas\n")
display(date())
fprintf("============================================================\n\n")
% ========================================================================
format short e
% Defining the function
f = @(x) x*sin(3.5*x) ;
df = @(x) sin(3.5*x) + 3.5*x*cos(3.5*x) ;
x = 1.35 ;
for i = 1:20
del(i,1)= 10^(-i);
backward(i,1) = (f(x)-f(x-del(i,1)))/del(i,1);
forward(i,1) = (f(x+del(i,1))-f(x))/del(i,1);
central(i,1) = (f(x+del(i,1))-f(x-del(i,1)))/(2*del(i,1));
error_backward(i,1) = abs(backward(i,1)-df(x));
error_forward(i,1) = abs(forward(i,1)-df(x));
error_central(i,1) = abs(central(i,1)-df(x));
end
disp(x)
% Plot the error vs del x for each method on the log scale
figure
hold on
% Scale of log for axis
set(gca, 'XScale', 'log', 'YScale', 'log')
% the loglog() function is the same as plot() but on log scale for both axes
loglog(del,error_backward)
loglog(del,error_forward)
loglog(del, error_central)
xlabel('\Delta'), ylabel('Error')
title('Error on Fordward, Backward, and Central')
legend('Backward','Forward','Central')
grid on, hold off