%% Your name, project name, and date
fprintf("============================================================\n")
fprintf("Project 2 - finding the root of a scalar equation\n")
fprintf("Sebastian Rivas\n")
display(date())
fprintf("============================================================\n\n")
%% Clear history
clc, clear, close all;
%% Set Variables
L=1500;
D=24;
r=3.5*10^-4;
V=.45;
R = 8.1818*10^4;
g=32.2;
%% Set functions
f = @(x) x^-.5+2.0*log10((r/3.7)+(2.51/(R*(x^.5))));
df = @(x) -.5*x^(-3/2)-(x^(-3/2))*((2.51/R)*log10(e)/((r/3.7)+(2.51/(R*(x^.5)))));
h=@(f) f((L*(V^2))/(D*2*g));
%% Iteration setting
max_iter = ;
guess= ;
res_tol = ;
conv_tol = ;
%% plot the function (visually see the root)
x = 0.0001:0.0001:0.1;
fval = f(x);
figure
plot(x, fval, x, zeros(length(x)))
title('Function to find the root')
%% Run the solvers
% Newton Raphson for four gusses
fprintf('Newton Raphson\n')
% call the newton_raphson() function here
newton_raphson_func(f,df,guess,conv_tol,res_tol,max_iter)
fprintf('\n==========================================================\n')
% Secant
fprintf('Secant\n')
% call the secant() function here
%% Printing Answers
fprintf('\n==========================================================\n')
fprintf('Answers:\n')
% Friction Factor
fprintf('\nFriction Factor:\n')
% If Diverged
if
fprintf(' newton of (guess = %0.6f) = Diverged! \n',....)
end
% If Converged
if
fprintf(' newton of (guess = %0.6f) = %.12f in %i iterations.
\n',... ,.... ,.... );
end
fprintf(' secant (guess = %0.6f and %0.6f) = %.12f in %i iterations.
\n',....,....,....,....);
% MATLAB root finder
fprintf('\nMATLAB fzero: \n')
x_initial = 0.1; % initial guess
root = fzero(func, x_initial); % call root solver (func is function program of the
friction factor)
% Head Loss (call back head loss function for friction factor)
fprintf("\nHead Loss\n")