function [x, conv, res, i] = ...
newton_raphson_function(f, df, initial_guess, conv_tol, res_tol, max_iter)
% initial guess
x(1) = initial_guess;
% initial convergence
conv(1) = conv_tol;
% initial residual
res(1) = res_tol;
fprintf('iteration x residual convergence\n');
fprintf('========= ===== ========= ==========\n');
fprintf(' %2i %.8e %.4e %.4e\n', 0,x(1),res(1),conv(1));
% initialize the iteration counter
i = 1;
% iterate using our formula
while i<max_iter
fval = f;
dfval = df;
if (dfval==0) || (dfval==NaN)
error("!!! FAILED. The derivative value is %i. Try another guess.", dfval)
break;
end
x(i+1) = ; % apply Newton-Raphson formula
conv(i+1) = ; % calculate iterative convergence
res(i+1) = ; % calculate the residual
fprintf(' %i %.8e %.4e %.4e\n', ...
i,x(i+1),res(i+1),conv(i+1));
% check for convergence
if &&
break;
end
% Check for divergence
if ||
break;
end
i=i+1; % increment our iteration counter
end
end