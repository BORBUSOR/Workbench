function[]=diagDom(A)

nlength(A);
for i=1:n 
    if abs(A(i,i))<sum(abs(A(i,:))-abs(A(i,i)))
        fprintf('Not Strictly Diagonally Dominant\n')
        break
    else 
        fprintf('Is Strictly Diagonally Dominant\n')
    end
end