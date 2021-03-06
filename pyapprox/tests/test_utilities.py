import unittest
from pyapprox.utilities import *
from pyapprox.univariate_quadrature import gauss_jacobi_pts_wts_1D
from scipy.linalg import lu_factor, lu as scipy_lu

class TestUtilities(unittest.TestCase):

    def setUp(self):
        np.random.seed(1)

    def test_cartesian_product(self):
        # test when num elems = 1
        s1 = np.arange( 0, 3 )
        s2 = np.arange( 3, 5 )

        sets = np.array( [[0,3], [1,3], [2,3], [0,4],
                                [1,4], [2,4]], np.int )
        output_sets = cartesian_product( [s1,s2], 1 )
        assert np.array_equal( output_sets.T, sets )

        # # test when num elems > 1
        # s1 = np.arange( 0, 6 )
        # s2 = np.arange( 6, 10 )

        # sets = np.array( [[ 0, 1, 6, 7], [ 2, 3, 6, 7],
        #                   [ 4, 5, 6, 7], [ 0, 1, 8, 9],
        #                   [ 2, 3, 8, 9], [ 4, 5, 8, 9]], np.int )
        # output_sets = cartesian_product( [s1,s2], 2 )
        # assert np.array_equal( output_sets.T, sets )

    def test_outer_product(self):
        s1 = np.arange( 0, 3 )
        s2 = np.arange( 3, 5 )

        test_vals = np.array( [0.,3.,6.,0.,4.,8.])
        output = outer_product( [s1,s2] )
        assert np.allclose( test_vals, output )

        output = outer_product( [s1] )
        assert np.allclose( output, s1 )

        
    def test_truncated_pivoted_lu_factorization(self):
        np.random.seed(2)
        # test truncated_pivoted lu factorization
        A = np.random.normal( 0, 1, (4,4) )
        scipy_LU, scipy_p  = lu_factor(A)
        scipy_pivots = get_final_pivots_from_sequential_pivots(scipy_p)
        num_pivots = 3
        L, U, pivots = truncated_pivoted_lu_factorization(A, num_pivots)
        assert np.allclose( pivots, scipy_pivots[:num_pivots] )
        assert np.allclose(A[pivots, :num_pivots], np.dot(L, U))
        P = get_pivot_matrix_from_vector(pivots,A.shape[0])
        assert np.allclose(P.dot(A[:, :num_pivots]), np.dot(L, U))

        # test truncated_pivoted lu factorization which enforces first
        # n rows to be chosen in exact order
        # mess up array so that if pivots are not enforced correctly a different
        # pivot order would be returne, Put best pivot in last place in matrix
        # and worst in first row, then enforce first and second rows to be chosen
        # first.
        tmp = A[pivots[0], :].copy()
        A[pivots[0],:] = A[pivots[-1], :].copy()
        A[pivots[-1],:] = tmp
        num_pivots = 3
        num_initial_rows = np.array([0, 1])
        L,U,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, num_initial_rows )
        assert np.allclose(A[pivots, :num_pivots], np.dot(L, U))
        assert np.allclose(pivots, [0, 1, 3])

        # test truncated_pivoted lu factorization which enforces first
        # n rows to be chosen in any order
        tmp = A[pivots[0], :].copy()
        A[pivots[0], :] = A[0,: ].copy()
        A[0,:] = tmp
        num_pivots = 3
        num_initial_rows = 1
        L,U,pivots = truncated_pivoted_lu_factorization(A, num_pivots, 
                                                        num_initial_rows)
        assert np.allclose(A[pivots, :num_pivots], np.dot(L, U))
        assert np.allclose(pivots, [0, 3, 1])

        # Modify the above test to first factorize 4,3 A then factorize
        # B = [A; C] where C is 2*3 and if B was factorized without enforcing
        # A then the factors would be different. Then check that first 
        # 4 rows of LU factors of B are the same as when A was factored.

    def test_tensor_product_quadrature(self):
        num_vars = 2
        alpha_poly=1
        beta_poly=2
        def univariate_quadrature_rule(n):
            x,w = gauss_jacobi_pts_wts_1D(n,alpha_poly,beta_poly)
            x=(x+1)/2.
            return x,w
        
        x,w = get_tensor_product_quadrature_rule(
            100,num_vars,univariate_quadrature_rule)
        function = lambda x: np.sum(x**2,axis=0)
        assert np.allclose(np.dot(function(x),w),0.8)

        #samples = np.random.beta(beta_poly+1,alpha_poly+1,(num_vars,10000))
        #print function(samples).mean()

    def test_canonical_piecewise_quadratic_interpolation(self):
        num_mesh_points=101
        mesh = np.linspace(0.,1.,3)
        mesh_vals = mesh**2
        #do not compare at right boundary because it will be zero
        interp_mesh = np.linspace(0.,1.,num_mesh_points)[:-1]
        interp_vals=canonical_piecewise_quadratic_interpolation(
            interp_mesh,mesh_vals)
        assert np.allclose(interp_vals,interp_mesh**2)

    def test_piecewise_quadratic_interpolation(self):
        def function(x):
            return (x-0.5)**3
        num_mesh_points = 301
        mesh = np.linspace(0.,1.,num_mesh_points)
        mesh_vals = function(mesh)
        #interp_mesh = np.random.uniform(0.,1.,101)
        interp_mesh = np.linspace(0.,1.,1001)
        ranges = [0,1]
        interp_vals=piecewise_quadratic_interpolation(
            interp_mesh,mesh,mesh_vals,ranges)
        # print np.linalg.norm(interp_vals-function(interp_mesh))
        # import pylab as plt
        # I= np.argsort(interp_mesh)
        # plt.plot(interp_mesh[I],interp_vals[I],'k-')
        # plt.plot(mesh,mesh_vals,'o')
        # plt.show()
        assert np.linalg.norm(interp_vals-function(interp_mesh))<1e-6

    def test_add_columns_to_pivoted_lu_factorization(self):
        """
        Let 
        A  = [1 2 4]
             [2 1 3]
             [3 2 4]

        Recursive Algorithm
        -------------------
        The following Permutation swaps the thrid and first rows
        P1 = [0 0 1]
             [0 1 0]
             [1 0 0]

        Gives
        P1*A  = [3 2 4]
                [2 1 3]
                [1 2 4]

        Conceptually partition matrix into block matrix
        P1*A = [A11 A12]
               [A21 A22]

             = [1    0 ][u11 U12]
               [L21 L22][ 0  U22]
             = [u11           U12      ]
               [u11*L21 L21*U12+L22*U22]

        Then 
        u11 = a11
        L21 = 1/a11 A21
        U12 = A12

        e.g. 
        a11 = 3  L21 = [2/3]  U12 = [2 4]  u11 = 3
                       [1/3]

        Because A22 = L21*U12+L22*U22
        L22*U22 = A22-L21*U12
        We also know L22=I

        LU sublock after 1 step is 
        S1 = L22*U22 = A22-L21*U12

           = [1 3]-[4/3 8/3] = [-1/3 1/3]
             [2 4] [2/3 4/3]   [ 4/3 8/3]

        LU after 1 step is
        LU1 = [u11 U12]
              [L21 S1 ]

              [3     2   4  ]
            = [1/3 -1/3 1/3 ]
              [2/3  4/3 8/32]

        The following Permutation swaps the first and second rows of S1
        P2 = [0 1]
             [1 0]

        Conceptually partition matrix into block matrix
        P2*S1 = [ 4/3 8/3] = [A11 A12]
                [-1/3 1/3] = [A21 A22] 

        L21 = 1/a11 A21
        U12 = A12

        e.g. 
        a11 = 4/3   L21 = [-1/4]  U12 = [8/3] u11 = 4/3

        LU sublock after 1 step is 
        S2 = A22-L21*U12
           = 1/3 + 1/4*8/3 = 1

        LU after 2 step is
        LU2 = [ 3    2   4 ]
              [1/3  u11 U12]
              [2/3  L21 S2 ]

            = [ 3    2   4 ]
              [1/3  4/3 8/3]
              [2/3 -1/4 S2 ]
    

        Matrix multiplication algorithm
        -------------------------------
        The following Permutation swaps the thrid and first rows
        P1 = [0 0 1]
             [0 1 0]
             [1 0 0]

        Gives
        P1*A  = [3 2 4]
                [2 1 3]
                [1 2 4]

        Use Matrix M1 to eliminate entries in second and third row of column 1
             [  1  0 1]
        M1 = [-2/3 1 0]
             [-1/3 0 1]

        So U factor after step 1 is
        U1  = M1*P1*A

              [3   2   4  ]
            = [0 -1/3 1/3 ]
              [0  4/3 8/32]

        The following Permutation swaps the third and second rows
        P2 = [1 0 0]
             [0 0 1]
             [0 1 0]

        M2 = [1  0  0]
             [0  1  0]
             [0 1/4 1]

        U factor after step 2 is
        U2  = M2*P2*M1*P1*A

              [3  2   4  ]
            = [0 4/3 8/3 ]
              [0  0   1  ]

        L2 = (M2P2M1P1)^{-1}
           = [ 1    0  0]
             [1/3   1  0]
             [2/3 -1/4 1]

        P*A = P2*P1*A = L2U2   
        """
        A = np.random.normal( 0, 1, (6,6) )
            
        num_pivots = 6
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False)

        
        LU_factor_init,pivots_init = \
          truncated_pivoted_lu_factorization(
            A[:,:num_pivots], num_pivots, truncate_L_factor=False)

        new_cols = A[:,LU_factor_init.shape[1]:].copy()

        LU_factor_final=add_columns_to_pivoted_lu_factorization(
            LU_factor_init,new_cols,pivots_init[:num_pivots])
        assert np.allclose(LU_factor_final,LU_factor)

        A = np.random.normal( 0, 1, (6,6) )
            
        num_pivots = 2
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False)

        
        LU_factor_init,pivots_init = \
          truncated_pivoted_lu_factorization(
            A[:,:num_pivots], num_pivots, truncate_L_factor=False)

        new_cols = A[:,LU_factor_init.shape[1]:].copy()

        LU_factor_final=add_columns_to_pivoted_lu_factorization(
            LU_factor_init,new_cols,pivots_init[:num_pivots])
        assert np.allclose(LU_factor_final,LU_factor)


    def test_split_lu_factorization_matrix(self):
        A = np.random.normal( 0, 1, (4,4) )
        num_pivots = A.shape[0]
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False)
        L_factor,U_factor = split_lu_factorization_matrix(LU_factor)
        assert np.allclose(L_factor.dot(U_factor),pivot_rows(pivots,A,False))

        A = np.random.normal( 0, 1, (4,4) )
        num_pivots = 2
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False)

        L_factor,U_factor = split_lu_factorization_matrix(LU_factor,num_pivots)
        assert np.allclose(L_factor.dot(U_factor),pivot_rows(pivots,A,False))

    def test_add_rows_to_pivoted_lu_factorization(self):

        np.random.seed(3)
        A = np.random.normal( 0, 1, (10,3) )
           
        num_pivots = A.shape[1]
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False)

        # create matrix for which pivots do not matter
        A = pivot_rows(pivots,A,False)
        # check no pivoting is necessary
        L,U,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=True)
        assert np.allclose(pivots,np.arange(num_pivots))

        LU_factor_init,pivots_init = \
          truncated_pivoted_lu_factorization(
            A[:num_pivots,:], num_pivots, truncate_L_factor=False)
         
        new_rows = A[num_pivots:,:].copy()

        LU_factor_final=add_rows_to_pivoted_lu_factorization(
            LU_factor_init,new_rows,num_pivots)
        assert np.allclose(LU_factor_final,LU_factor)

        #######
        # only pivot some of the rows
        
        A = np.random.normal( 0, 1, (10,5) )
           
        num_pivots = 3
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False)

        # create matrix for which pivots do not matter
        A = pivot_rows(pivots,A,False)
        print(A.shape)
        # check no pivoting is necessary
        L,U,pivots = truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=True)
        assert np.allclose(pivots,np.arange(num_pivots))

        LU_factor_init,pivots_init = \
          truncated_pivoted_lu_factorization(
            A[:num_pivots,:], num_pivots, truncate_L_factor=False)
         
        new_rows = A[num_pivots:,:].copy()

        LU_factor_final=add_rows_to_pivoted_lu_factorization(
            LU_factor_init,new_rows,num_pivots)
        assert np.allclose(LU_factor_final,LU_factor)

    def test_unprecondition_LU_factor(self):
        A = np.random.normal( 0, 1, (4,4) )
        num_pivots = A.shape[0]
        precond_weights = 1/np.linalg.norm(A,axis=1)[:,np.newaxis]
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A*precond_weights, num_pivots, truncate_L_factor=False)

        unprecond_LU_factor,unprecond_pivots=truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False,
            num_initial_rows=pivots)
        L_unprecond,U_unprecond = split_lu_factorization_matrix(
            unprecond_LU_factor)
        assert np.allclose(unprecond_pivots,pivots)
        assert np.allclose(
            L_unprecond.dot(U_unprecond),pivot_rows(unprecond_pivots,A,False))

        precond_weights = pivot_rows(pivots,precond_weights,False)

        L,U = split_lu_factorization_matrix(LU_factor)
        W = np.diag(precond_weights[:,0])
        Wi = np.linalg.inv(W)
        assert np.allclose(Wi.dot(L).dot(U),pivot_rows(pivots,A,False))
        assert np.allclose(
            (L/precond_weights).dot(U),pivot_rows(pivots,A,False))
        # inv(W)*L*W*inv(W)*U
        L = L/precond_weights*precond_weights.T
        U = U/precond_weights
        assert np.allclose(L.dot(U),pivot_rows(pivots,A,False))
        assert np.allclose(L,L_unprecond)
        assert np.allclose(U,U_unprecond)
        
        LU_factor = unprecondition_LU_factor(LU_factor,precond_weights)
        assert np.allclose(LU_factor,unprecond_LU_factor)
       
        A = np.random.normal( 0, 1, (4,4) )
        num_pivots = 2
        precond_weights = 1/np.linalg.norm(A,axis=1)[:,np.newaxis]
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A*precond_weights, num_pivots, truncate_L_factor=False)
        L,U = split_lu_factorization_matrix(LU_factor,num_pivots)
        assert np.allclose(
            L.dot(U),pivot_rows(pivots[:num_pivots],A*precond_weights,False))

        unprecond_LU_factor,unprecond_pivots=truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False,
            num_initial_rows=pivots)
        L_unprecond,U_unprecond = split_lu_factorization_matrix(
            unprecond_LU_factor,num_pivots)
        assert np.allclose(unprecond_pivots,pivots)
        assert np.allclose(
            L_unprecond.dot(U_unprecond),
            pivot_rows(unprecond_pivots[:num_pivots],A,False))

        precond_weights = pivot_rows(pivots,precond_weights,False)
        LU_factor = unprecondition_LU_factor(
            LU_factor,precond_weights,num_pivots)
        assert np.allclose(LU_factor,unprecond_LU_factor)

        A = np.random.normal( 0, 1, (5,4) )
        num_pivots = 3
        precond_weights = 1/np.linalg.norm(A,axis=1)[:,np.newaxis]
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A*precond_weights, num_pivots, truncate_L_factor=False)
        L,U = split_lu_factorization_matrix(LU_factor,num_pivots)
        assert np.allclose(
            L.dot(U),pivot_rows(pivots[:num_pivots],A*precond_weights,False))

        unprecond_LU_factor,unprecond_pivots=truncated_pivoted_lu_factorization(
            A, num_pivots, truncate_L_factor=False,
            num_initial_rows=pivots)
        L_unprecond,U_unprecond = split_lu_factorization_matrix(
            unprecond_LU_factor,num_pivots)
        assert np.allclose(unprecond_pivots,pivots)
        assert np.allclose(
            L_unprecond.dot(U_unprecond),
            pivot_rows(unprecond_pivots[:num_pivots],A,False))

        precond_weights = pivot_rows(pivots,precond_weights,False)
        LU_factor = unprecondition_LU_factor(
            LU_factor,precond_weights,num_pivots)
        assert np.allclose(LU_factor,unprecond_LU_factor)

    def check_LU_factor(self,LU_factor,pivots,num_pivots,A):
        L,U = split_lu_factorization_matrix(LU_factor,num_pivots)
        return np.allclose(L.dot(U),pivot_rows(pivots,A,False))


    def test_update_christoffel_preconditioned_lu_factorization(self):
        np.random.seed(3)
        A = np.random.normal( 0, 1, (4,4) )

        precond_weights = 1/np.linalg.norm(A,axis=1)[:,np.newaxis]
           
        num_pivots = A.shape[1]
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A*precond_weights, num_pivots, truncate_L_factor=False)

        # create matrix for which pivots do not matter
        A_precond = pivot_rows(pivots,A*precond_weights,False)
        # check no pivoting is necessary
        L,U,pivots = truncated_pivoted_lu_factorization(
            A_precond, num_pivots, truncate_L_factor=True)
        assert np.allclose(pivots,np.arange(num_pivots))

        ii=1
        A_sub = A[:,:ii].copy()
        precond_weights = 1/np.linalg.norm(A_sub,axis=1)[:,np.newaxis]
        A_sub *= precond_weights
        LU_factor,pivots = truncated_pivoted_lu_factorization(
            A_sub, num_pivots, truncate_L_factor=False)
        for ii in range(2,A.shape[1]):
            A_sub = A[:,:ii].copy()
            precond_weights_prev = precond_weights.copy()
            precond_weights = 1/np.linalg.norm(A_sub,axis=1)[:,np.newaxis]
            pivots_prev = pivots.copy()
            pivoted_precond_weights_prev = pivot_rows(
                pivots_prev,precond_weights_prev,False)
            pivoted_precond_weights = pivot_rows(pivots,precond_weights,False)
            
            # what is factorization using old precond weights but with
            # extra column
            true_LU_factor_extra_cols,p= truncated_pivoted_lu_factorization(
                A_sub*precond_weights_prev, ii-1, truncate_L_factor=False,
                num_initial_rows=pivots_prev)
            assert np.allclose(p,pivots_prev)
            assert self.check_LU_factor(
                true_LU_factor_extra_cols,pivots_prev,ii-1,
                A_sub*precond_weights_prev)
            new_cols = A_sub[:,ii-1:ii].copy()
            new_cols*=precond_weights_prev
            LU_factor = add_columns_to_pivoted_lu_factorization(
                LU_factor.copy(),new_cols,pivots_prev[:ii-1])
            assert np.allclose(LU_factor,true_LU_factor_extra_cols)
            assert self.check_LU_factor(
                LU_factor,pivots_prev,ii-1,A_sub*precond_weights_prev)

            # what is factorization with extra column but no preconditioning
            true_LU_factor_extra_cols_unprecond,p = \
                truncated_pivoted_lu_factorization(
                    A_sub, ii-1, truncate_L_factor=False,
                    num_initial_rows=pivots_prev)
            assert np.allclose(p,pivots_prev)
            assert self.check_LU_factor(
                true_LU_factor_extra_cols_unprecond,pivots_prev,ii-1,A_sub)
            LU_factor_unprecond = unprecondition_LU_factor(
                LU_factor,pivoted_precond_weights_prev,ii-1)
            assert self.check_LU_factor(
                LU_factor_unprecond,pivots_prev,ii-1,A_sub)            
            assert np.allclose(
                LU_factor_unprecond,true_LU_factor_extra_cols_unprecond)

            # what is factorization using new precond weights and
            # extra column
            true_LU_factor_extra_cols,_= truncated_pivoted_lu_factorization(
                A_sub*precond_weights, ii-1, truncate_L_factor=False,
                num_initial_rows=pivots_prev)
            LU_factor = unprecondition_LU_factor(
                LU_factor,pivoted_precond_weights_prev/pivoted_precond_weights,
                ii-1)
            assert np.allclose(LU_factor,true_LU_factor_extra_cols)

            max_iters = A_sub.shape[1]
            LU_factor,pivots,it = continue_pivoted_lu_factorization(
                LU_factor.copy(),pivots_prev,ii-1,max_iters,num_initial_rows=0)

            true_LU_factor,_= truncated_pivoted_lu_factorization(
                A_sub*precond_weights, num_pivots, truncate_L_factor=False,
                num_initial_rows=pivots)
            assert np.allclose(LU_factor,true_LU_factor)

    def test_cholesky_decomposition(self):
        nrows = 4
        A = np.random.normal(0.,1.,(nrows,nrows))
        A = A.T.dot(A)
        L_np = np.linalg.cholesky(A)
        L = cholesky_decomposition(A)

    def test_pivoted_cholesky_decomposition(self):
        nrows, npivots = 4, 4
        A = np.random.normal(0., 1., (nrows, nrows))
        A = A.T.dot(A)
        L, pivots, error, flag = pivoted_cholesky_decomposition(A, npivots)
        assert np.allclose(L.dot(L.T), A)

        nrows, npivots = 4, 2
        A = np.random.normal(0., 1., (npivots, nrows))
        A = A.T.dot(A)
        L, pivots, error, flag = pivoted_cholesky_decomposition(A, npivots)
        assert L.shape == (nrows, npivots)
        assert pivots.shape[0] == npivots
        assert np.allclose(L.dot(L.T), A)

        # check init_pivots are enforced
        nrows, npivots = 4, 2
        A = np.random.normal(0., 1., (npivots+1, nrows))
        A = A.T.dot(A)
        L, pivots, error, flag = pivoted_cholesky_decomposition(A, npivots+1)
        L, new_pivots, error, flag = pivoted_cholesky_decomposition(
            A,npivots+1, init_pivots=pivots[1:2])
        assert np.allclose(new_pivots[:npivots+1], pivots[[1,0,2]])

        L = L[pivots, :]
        assert np.allclose(A[pivots, :][:, pivots], L.dot(L.T))

        assert np.allclose(A[np.ix_(pivots, pivots)], L.dot(L.T))

        P = get_pivot_matrix_from_vector(pivots,nrows)
        assert np.allclose(P.dot(A).dot(P.T), L.dot(L.T))

        A = np.array([[4, 12, -16], [12, 37 ,-43], [-16, -43, 98.]])
        L, pivots, error, flag = pivoted_cholesky_decomposition(A, A.shape[0])

        # reorder entries of A so that cholesky requires pivoting
        true_pivots = np.array([2, 1, 0])
        A_no_pivots = A[true_pivots, :][:, true_pivots]
        L_np = np.linalg.cholesky(A_no_pivots)
        assert np.allclose(L[pivots, :], L_np)

        # Create A with which needs cholesky with certain pivots
        A = np.array([[4, 12, -16], [12, 37, -43], [-16, -43, 98.]])
        true_pivots = np.array([1, 0, 2])
        A = A[true_pivots, :][:, true_pivots]
        L, pivots, error, flag = pivoted_cholesky_decomposition(A, A.shape[0])
        assert np.allclose(L[pivots, :], L_np)

    def test_restart_pivoted_cholesky(self):
        nrows = 10
        A = np.random.normal(0,1,(nrows,nrows))
        A = A.T.dot(A)

        pivot_weights = np.random.uniform(1,2,A.shape[0])
        L, pivots, error, flag = pivoted_cholesky_decomposition(
            A, A.shape[0], pivot_weights=pivot_weights)

        npivots = A.shape[0]-2
        full_L, full_pivots, full_error, flag, diag, init_error, \
            ncompleted_pivots = pivoted_cholesky_decomposition(
                A, npivots, return_full=True, pivot_weights=pivot_weights)
        assert ncompleted_pivots==npivots

        import time
        t0 = time.time()
        npivots = A.shape[0]
        full_L, full_pivots, diag, chol_flag, ii, error = \
            continue_pivoted_cholesky_decomposition(
                A, full_L, npivots, None, 0, True, pivot_weights,
                full_pivots, diag, ncompleted_pivots, init_error, econ=True)
        #print(time.time()-t0)

        assert np.allclose(L,full_L)
        assert np.allclose(pivots,full_pivots)

    def test_update_cholesky_decomposition(self):
        nvars = 5
        B = np.random.normal(0, 1, (nvars,nvars))
        A = B.T.dot(B)

        L = np.linalg.cholesky(A)
        A_11 = A[:nvars-2, :nvars-2]
        A_12 = A[:nvars-2, nvars-2:]
        A_22 = A[nvars-2:, nvars-2:]
        assert np.allclose(np.block([[A_11, A_12], [A_12.T, A_22]]), A)
        L_11 = np.linalg.cholesky(A_11)
        L_up = update_cholesky_factorization(L_11, A_12, A_22)
        assert np.allclose(L, L_up)

        L_inv = np.linalg.inv(L)
        L_11_inv = np.linalg.inv(L_11)
        L_12_T = L[L_11.shape[0]:, :L_11.shape[1]]
        L_12 = L_12_T.T
        L_22 = L[L_11.shape[0]:, L_11.shape[0]:]
        assert np.allclose(
            L_inv, update_cholesky_factorization_inverse(L_11_inv, L_12, L_22))

        L_22_inv = np.linalg.inv(L_22)
        C = -np.dot(L_22_inv.dot(L_12.T), L_11_inv)
        A_inv = np.block(
            [[L_11_inv.T.dot(L_11_inv)+C.T.dot(C),C.T.dot(L_22_inv)],
             [L_22_inv.T.dot(C), L_22_inv.T.dot(L_22_inv)]])
        assert np.allclose(A_inv, np.linalg.inv(A))

        
        N = np.random.normal(0, 1, A.shape)
        assert np.allclose(np.trace(np.linalg.inv(A).dot(B)), np.sum(A_inv*B))

        B_11 = B[:A_11.shape[0], :A_11.shape[1]]
        prev_trace = np.trace(np.linalg.inv(A_11).dot(B_11))
        trace = update_trace_involving_cholesky_inverse(
            L_11_inv, L_12, L_22_inv, B, prev_trace)
        assert np.allclose(trace, np.trace(np.linalg.inv(A).dot(B)))

        x = np.random.normal(0, 1, (nvars))
        y = solve_triangular(L, x, lower=True)
        z = solve_triangular(L.T, y, lower=False)

        x_1 = x[:L_11.shape[0]]
        y_1 = solve_triangular(L_11, x_1, lower=True)
        z_1 = solve_triangular(L_11.T, y_1, lower=False)

        x_up_1 = x_1
        x_up_2 = x[L_11.shape[0]:]
        y_up_1 = y_1
        y_up_2 = solve_triangular(L_22, x_up_2-L_12_T.dot(y_up_1), lower=True)
        assert np.allclose(y_up_1, y[:L_11.shape[0]])
        assert np.allclose(y_up_2, y[L_11.shape[0]:])
        z_up_2 = solve_triangular(L_22.T, y_up_2, lower=False)
        z_up_1 = solve_triangular(
            L_11.T, y_up_1 - L_12.dot(z_up_2), lower=False)
        assert np.allclose(z_up_2, z[L_11.shape[0]:])
        assert np.allclose(z_up_1, z[:L_11.shape[0]])
        assert np.allclose(
            z_up_1,
            z_1 - solve_triangular(L_11.T, L_12.dot(z_up_2), lower=False))

    def test_cholesky_decomposition_minimizing_trace_norm(self):
        """
        Test how to compute pivot that minimizes trace norm
        """
        n = 6
        B = np.random.normal(0, 1, (n, n))
        A = B.T.dot(B)
        # pivots = [1,2,0] causes issues with pya.pivoted_cholesky_decomposition

        if n == 4:
            a1 = A[2, 2]
            b1 = np.array([[A[1, 2], A[0, 2], A[3, 2]]]).T
            C1 = np.array([[A[1, 1], A[1, 0], A[1, 3]],
                           [A[0, 1], A[0, 0], A[0, 3]],
                           [A[3, 1], A[3, 0], A[3, 3]]])
            S1 = C1 - b1.dot(b1.T)/a1
            L1 = np.zeros((n, n))
            pivots1 = np.array([2,1,0,3])
            L1[pivots1, 0] = A[pivots1[0], :]/np.sqrt(a1)
            assert np.allclose(A[np.ix_(pivots1, pivots1)][1:, 1:], C1)
            assert np.allclose(L1[:1, :1].dot(L1[:1, :1].T), A[2, 2])

            raw_pivots2 = np.array([1, 0, 2]) # choose first remaining pivot
            S2 = S1[np.ix_(raw_pivots2, raw_pivots2)]
            a2 = S2[0, 0]
            b2 = S2[1:, 0:1]
            C2 = S2[1:, 1:]
            S2 = C2 - b2.dot(b2.T)/a2
            L2 = L1.copy()
            swap_rows(L2, 1, raw_pivots2[0]+1)
            L2[1:, 1:2] = np.vstack([[[a2]],b2])/np.sqrt(a2)
            pivots = np.hstack([pivots1[0], pivots1[1:][raw_pivots2]])
            assert np.allclose(
                L2.dot(L2.T)[:2, :2], A[np.ix_(pivots[:2], pivots[:2])])

            a_list = [a1, a2]
            b_list = [b1, b2]
            C_list = [C1, C2]
            S_list = [S1, S2]

        trace_A = np.trace(A)
        S = A.copy()
        lvecs = np.zeros(A.shape)
        Smats = []
        traces = [0]
        pivots = np.arange(n)
        #use_pivoting = False
        use_pivoting = True
        for ii in range(n):
            # Given a new l vector we have
            # A_ii = [L  l ] [L.T] = L.dot(L.T)+l.dot(l.T)
            #                [l.T]
            # Thus trace(A_ii) = trace(L.dot(L.T)+l.dot(l.T))
            #                  = trace(L.dot(L.T))+trace(l.dot(l.T))

            pivot_vals = np.linalg.norm(S[:, :], axis=0)**2/np.diag(S)
            if use_pivoting is True:
                raw_pivot = np.argmax(pivot_vals)
            else:
                raw_pivot = 0  # do not pivot

            traces.append(traces[-1]+pivot_vals[raw_pivot])
            pivot = raw_pivot+ii
            S_pivots = np.arange(S.shape[0])
            swap_rows(S_pivots, 0, raw_pivot)
            S = S[np.ix_(S_pivots, S_pivots)]

            a = S[0, 0]
            indices = np.arange(1, S.shape[0])
            b = S[1:, 0:1].copy()
            C = S[1:, 1:].copy()
            nonzero_l = np.vstack([[[a]], b])/np.sqrt(a)
            swap_rows(lvecs, ii, pivot)
            lvecs[ii:, ii:ii+1] = nonzero_l
            swap_rows(pivots, ii, pivot)

            L_ii = lvecs[:, :ii+1]
            trace_S = trace_A - (
                np.trace(L_ii[:, :-1].dot(L_ii[:, :-1].T))+
                np.linalg.norm(S[:, 0])**2/S[0, 0])

            S = C-1/a*(b.dot(b.T))
            if ii < 2 and n == 4:
                assert np.allclose(C, C_list[ii])
                assert np.allclose(b, b_list[ii])
                assert np.allclose(a, a_list[ii])
                assert np.allclose(S, S_list[ii])
                assert np.allclose(S, S.T)
            Smats.append(S)
            A_ii = L_ii.dot(L_ii.T)
            assert np.allclose(
                A[np.ix_(pivots[:ii+1], pivots[:ii+1])], A_ii[:ii+1, :ii+1])
            assert np.allclose(
                (A[np.ix_(pivots, pivots)]-A_ii)[ii+1:, ii+1:], S)
            assert np.allclose(
                np.trace(A), np.trace(A_ii)+np.trace(S))
            assert np.allclose(
                np.trace(S), np.trace(A)-np.trace(A_ii))
            assert np.allclose(trace_S, np.trace(S))
            assert np.allclose(trace_A-traces[-1], np.trace(S))

        L_chol = np.linalg.cholesky(A[np.ix_(pivots, pivots)])
        assert np.allclose(L_chol, lvecs)

        L1, pivots1, error1, flag1 = pivoted_cholesky_decomposition(
            A, A.shape[0], econ=True, init_pivots=pivots)
        assert np.allclose(L_chol, L1[pivots])

        if use_pivoting is False:
            # This check only good if pivoting is not enforced
            for ii in range(n):
                E = A-L_chol[:, :ii+1].dot(L_chol[:, :ii+1].T)
                assert np.allclose(E[ii+1:, ii+1:], Smats[ii])
        L2, pivots2, error2, flag2 = pivoted_cholesky_decomposition(
            A, A.shape[0], econ=False)
        assert np.allclose(L2[pivots2], L_chol)
        assert np.allclose(pivots1, pivots2)

    def test_beta_pdf_on_ab(self):
        from scipy.stats import beta as beta_rv
        alpha_stat,beta_stat = 5,2
        lb,ub=-2,1
        xx = np.linspace(lb,ub,100)
        vals = beta_pdf_on_ab(alpha_stat,beta_stat,lb,ub,xx)
        true_vals = beta_rv.pdf((xx-lb)/(ub-lb),alpha_stat,beta_stat)/(ub-lb)
        #true_vals = beta_rv.pdf(xx,alpha_stat,beta_stat,loc=lb,scale=ub-lb)
        assert np.allclose(vals,true_vals)

        import sympy as sp
        x = sp.Symbol('x')
        assert np.allclose(1,
            float(sp.integrate(beta_pdf_on_ab(alpha_stat,beta_stat,lb,ub,x),
                         (x,[lb,ub]))))

        alpha_stat,beta_stat = 5,2
        lb,ub=0,1
        xx = np.linspace(lb,ub,100)
        vals = beta_pdf_on_ab(alpha_stat,beta_stat,lb,ub,xx)
        true_vals = beta_rv.pdf((xx-lb)/(ub-lb),alpha_stat,beta_stat)/(ub-lb)
        assert np.allclose(vals,true_vals)

        import sympy as sp
        x = sp.Symbol('x')
        assert np.allclose(1,
            float(sp.integrate(beta_pdf_on_ab(alpha_stat,beta_stat,lb,ub,x),
                         (x,[lb,ub]))))

        eps=1e-7
        x = 0.5
        deriv = beta_pdf_derivative(alpha_stat,beta_stat,x)
        fd_deriv = (beta_pdf_on_ab(alpha_stat,beta_stat,0,1,x)-
                    beta_pdf_on_ab(alpha_stat,beta_stat,0,1,x-eps))/eps
        assert np.allclose(deriv,fd_deriv)

        eps=1e-7
        x = np.array([0.5,0,-0.25])
        from functools import partial
        pdf_deriv = partial(beta_pdf_derivative,alpha_stat,beta_stat)
        deriv = pdf_derivative_under_affine_map(
            pdf_deriv,-1,2,x)
        fd_deriv = (beta_pdf_on_ab(alpha_stat,beta_stat,-1,1,x)-
                    beta_pdf_on_ab(alpha_stat,beta_stat,-1,1,x-eps))/eps
        assert np.allclose(deriv,fd_deriv)

    def test_compute_f_divergence(self):
        # KL divergence
        from scipy.stats import multivariate_normal
        nvars=1
        mean = np.random.uniform(-0.1,0.1,nvars)
        cov  = np.diag(np.random.uniform(.5,1,nvars))
        rv1 = multivariate_normal(mean,cov)
        rv2 = multivariate_normal(np.zeros(nvars),np.eye(nvars))
        density1 = lambda x: rv1.pdf(x.T)
        density2 = lambda x: rv2.pdf(x.T)

        # Integrate on [-radius,radius]
        # Note this induces small error by truncating domain
        radius=10
        from pyapprox import get_tensor_product_quadrature_rule
        x,w=get_tensor_product_quadrature_rule(
            400,nvars,np.polynomial.legendre.leggauss,
            transform_samples=lambda x: x*radius,
            density_function=lambda x: radius*np.ones(x.shape[1]))
        quad_rule=x,w
        div = compute_f_divergence(density1,density2,quad_rule,'KL',
                                   normalize=False)
        true_div = 0.5*(np.diag(cov)+mean**2-np.log(np.diag(cov))-1).sum()
        assert np.allclose(div,true_div,rtol=1e-12)

        # Hellinger divergence
        from scipy.stats import beta
        a1,b1,a2,b2=1,1,2,3
        rv1,rv2 = beta(a1,b1),beta(a2,b2)
        true_div = 2*(1-beta_fn((a1+a2)/2,(b1+b2)/2)/np.sqrt(
            beta_fn(a1,b1)*beta_fn(a2,b2)))
        
        x,w=get_tensor_product_quadrature_rule(
            500,nvars,np.polynomial.legendre.leggauss,
            transform_samples=lambda x: (x+1)/2,
            density_function=lambda x: 0.5*np.ones(x.shape[1]))
        quad_rule=x,w
        div = compute_f_divergence(rv1.pdf,rv2.pdf,quad_rule,'hellinger',
                                   normalize=False)
        assert np.allclose(div,true_div,rtol=1e-10)

    def test_num_entries_triangular_matrix(self):
        M=4
        A=np.ones([M,M]); L = np.tril(A); 
        nentries = num_entries_square_triangular_matrix(
            M,include_diagonal=True)
        assert nentries == np.count_nonzero(L)

        M,N=4,3
        A=np.ones([M,N]); L = np.tril(A);
        nentries = num_entries_rectangular_triangular_matrix(
            M,N,upper=False)
        assert nentries == np.count_nonzero(L)

        A=np.ones([M,N]); U = np.triu(A);
        nentries = num_entries_rectangular_triangular_matrix(
            M,N,upper=True)
        assert nentries == np.count_nonzero(U)

    def test_flattened_rectangular_lower_triangular_matrix_index(self):

        M,N=4,3
        A=np.arange(M*N).reshape([M,N]); L = np.tril(A);
        tril_indices = np.tril_indices(M,m=N)
        tril_entries = A[tril_indices]
        #print(A)
        #print(tril_indices)
        #print(tril_entries)
        for nn in range(tril_indices[0].shape[0]):
            ii,jj=tril_indices[0][nn],tril_indices[1][nn]
            #print('#',ii,jj)
            kk = flattened_rectangular_lower_triangular_matrix_index(ii,jj,M,N)
            #print('kk',kk,tril_entries[nn])
            assert kk==nn

    def test_evaluate_quadratic_form(self):
        nvars,nsamples = 3,10
        A = np.random.normal(0,1,nvars)
        A = A.T.dot(A)
        samples = np.random.uniform(0, 1, (nvars,nsamples))
        values1 = evaluate_quadratic_form(A, samples)

        values2 = np.zeros(samples.shape[1])
        for ii in range(samples.shape[1]):
            values2[ii] = samples[:, ii:ii+1].T.dot(A).dot(samples[:, ii:ii+1])

        assert np.allclose(values1,values2)

    def test_weighted_pivoted_cholesky(self):
        nrows, npivots = 4, 3
        A = np.random.normal(0., 1., (nrows, nrows))
        A = A.T.dot(A)
        weights = np.random.uniform(1, 2, (nrows))
        L, pivots, error, flag = pivoted_cholesky_decomposition(
            A,npivots,pivot_weights=weights)

        B = np.diag(np.sqrt(weights)).dot(A.dot(np.diag(np.sqrt(weights))))
        C = np.sqrt(weights)[:,np.newaxis]*A*np.sqrt(weights)
        assert np.allclose(B,C)
        L2, pivots2, error2, flag2 = pivoted_cholesky_decomposition(
            C, npivots, pivot_weights=None)

        # check pivots are the same
        assert np.allclose(pivots, pivots2)

        # check cholesky factors are the same
        #we have L2.dot(L2.T)=S.dot(A).dot(S)= S.dot(L.dot(L.T)).dot(S)
        #where S = np.diag(np.sqrt(weights)). So L2=S.dot(L)
        assert np.allclose(
            np.sqrt(weights[pivots, np.newaxis])*L[pivots, :npivots],
            L2[pivots, :npivots])

    def cholesky_qr_pivoting_equivalence(self):
        nrows, npivots = 4, 4
        A = np.random.normal(0.,1.,(nrows,nrows))
        B = A.T.dot(A)
        cholL, chol_pivots, error, flag = pivoted_cholesky_decomposition(
            B,npivots)

        import scipy
        Q,R,P = scipy.linalg.qr(A,pivoting=True)
        assert np.allclose(P,chol_pivots)

        #print(R.T,'\n',cholL[chol_pivots])
        assert np.allclose(np.absolute(R.T),np.absolute(cholL[chol_pivots]))

    def test_least_sqaures_loo_cross_validation(self):
        degree = 2
        alpha = 1e-3
        nsamples = 2*(degree+1)
        samples = np.random.uniform(-1, 1, (1, nsamples))
        basis_mat = samples.T**np.arange(degree+1)
        values = np.exp(samples).T
        cv_errors, cv_score, coef = leave_one_out_lsq_cross_validation(
            basis_mat, values, alpha)
        true_cv_errors = np.empty_like(cv_errors)
        for ii in range(nsamples):
            samples_ii = np.hstack((samples[:, :ii], samples[:, ii+1:]))
            basis_mat_ii = samples_ii.T**np.arange(degree+1)
            values_ii = np.vstack((values[:ii], values[ii+1:]))
            coef_ii = np.linalg.lstsq(
                basis_mat_ii.T.dot(basis_mat_ii)+
                alpha*np.eye(basis_mat.shape[1]), basis_mat_ii.T.dot(values_ii),
                rcond=None)[0]
            true_cv_errors[ii] = (basis_mat[ii].dot(coef_ii)-values[ii])
        assert np.allclose(cv_errors, true_cv_errors)
        assert np.allclose(
            cv_score, np.sqrt(np.sum(true_cv_errors**2, axis=0)/nsamples))

    def test_leave_many_out_lsq_cross_validation(self):
        degree = 2
        nsamples = 2*(degree+1)
        samples = np.random.uniform(-1, 1, (1, nsamples))
        basis_mat = samples.T**np.arange(degree+1)
        values = np.exp(samples).T*100
        alpha = 1e-3 # ridge regression regularization parameter value

        assert nsamples%2 == 0
        nfolds = nsamples//3
        fold_sample_indices = get_random_k_fold_sample_indices(
            nsamples, nfolds)
        cv_errors, cv_score, coef = leave_many_out_lsq_cross_validation(
            basis_mat, values, fold_sample_indices, alpha)
        
        true_cv_errors = np.empty_like(cv_errors)
        for kk in range(len(fold_sample_indices)):
            K = np.ones(nsamples, dtype=bool)
            K[fold_sample_indices[kk]] = False
            basis_mat_kk = basis_mat[K, :]
            gram_mat_kk = basis_mat_kk.T.dot(basis_mat_kk) + np.eye(
                basis_mat_kk.shape[1])*alpha
            values_kk = basis_mat_kk.T.dot(values[K, :])
            coef_kk = np.linalg.lstsq(gram_mat_kk, values_kk, rcond=None)[0]
            true_cv_errors[kk] = basis_mat[fold_sample_indices[kk], :].dot(
                coef_kk)-values[fold_sample_indices[kk]]
        print(cv_errors, true_cv_errors)
        assert np.allclose(cv_errors, true_cv_errors)
        true_cv_score = np.sqrt((true_cv_errors**2).sum(axis=(0, 1))/nsamples)
        assert np.allclose(true_cv_score, cv_score)

        rsq = get_cross_validation_rsquared_coefficient_of_variation(
            cv_score, values)
        
        print(rsq)   
 
if __name__== "__main__":    
    utilities_test_suite = unittest.TestLoader().loadTestsFromTestCase(
        TestUtilities)
    unittest.TextTestRunner(verbosity=2).run(utilities_test_suite)
