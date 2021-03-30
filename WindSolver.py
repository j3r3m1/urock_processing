#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 14:57:25 2021

# Sandro Oswald, sandro.oswald@boku.ac.at
# Vienna Urban Climate Group
# University of natural sciences (BOKU)
"""
import numpy as np

def solver(dx, dy, dz, nx, ny, nz, un, vn, wn, u, v, w, buildIndexB, indices, iterations):
    H = nz / 1.
    L = nx / 1.
    B = ny / 1.

    x = np.linspace(0, L, nx)  # Range of x(0,L) and specifying grid points
    y = np.linspace(0, B, ny)  # Range of y(0,H) and specifying grid points
    z = np.linspace(0, H, nz)

    lambdaM = np.zeros([nx, ny, nz])  # Preallocating lambda
    lambdaM1 = np.zeros([nx, ny, nz])  # Preallocating lambda + 1

    lambdaM[0, :, :] = 0.
    lambdaM[:, 0, :] = 0.
    lambdaM[:, :, 0] = 0.
    lambdaM[-1, :, :] = 0.
    lambdaM[:, -1, :] = 0.
    lambdaM[:, :, -1] = 0.
    lambdaM1[0, :, :] = 0.
    lambdaM1[:, 0, :] = 0.
    lambdaM1[:, :, 0] = 0.
    lambdaM1[-1, :, :] = 0.
    lambdaM1[:, -1, :] = 0.
    lambdaM1[:, :, -1] = 0.

    #Xi = ((np.cos(np.pi / nx) + (dx / dy) ** 2 * np.cos(np.pi / ny)) / (1 + (dx / dy) ** 2)) ** 2

    omega = 1.78 #2. * ((1 - np.sqrt(1 - Xi)) / Xi)
    # if (omega < 1) or (omega > 2):
    #     omega = 1.78


    alphaH = 1.
    alphaV = 10.
    alpha = alphaH / alphaV

    e = np.ones([nx, ny, nz])
    f = np.ones([nx, ny, nz])
    g = np.ones([nx, ny, nz])
    h = np.ones([nx, ny, nz])
    m = np.ones([nx, ny, nz])
    n = np.ones([nx, ny, nz])
    o = np.ones([nx, ny, nz])
    p = np.ones([nx, ny, nz])
    q = np.ones([nx, ny, nz])


    e[buildIndexB[0], buildIndexB[1] - 1, buildIndexB[2]] = 0.
    f[buildIndexB[0], buildIndexB[1] + 1, buildIndexB[2]] = 0.
    g[buildIndexB[0] - 1, buildIndexB[1], buildIndexB[2]] = 0.
    h[buildIndexB[0] + 1, buildIndexB[1], buildIndexB[2]] = 0.
    # m[buildIndexB[0], buildIndexB[1], buildIndexB[2] - 1] = 0.
    n[buildIndexB[0], buildIndexB[1], buildIndexB[2] + 1] = 0.

    o[buildIndexB[0], buildIndexB[1] - 1, buildIndexB[2]] = 0.5
    o[buildIndexB[0], buildIndexB[1] + 1, buildIndexB[2]] = 0.5
    p[buildIndexB[0] - 1, buildIndexB[1], buildIndexB[2]] = 0.5
    p[buildIndexB[0] + 1, buildIndexB[1], buildIndexB[2]] = 0.5
    # q[buildIndexB[0], buildIndexB[1], buildIndexB[2] - 2] = 0.5
    q[buildIndexB[0], buildIndexB[1], buildIndexB[2] + 1] = 0.5


    Aj = dx ** 2 / dy ** 2
    Bk = alpha ** 2 * dx ** 2 / dz ** 2

    for index in range(iterations):

        lambdaM = np.copy(lambdaM1)

        #############
        for i, j, k in indices:

            lambdaM1[i, j, k] = omega * (
                    ((-1.) * (dx ** 2 * (-2. * alphaH ** 2) * (((un[i, j + 1, k] - un[i, j, k]) / (dx) + (
                            vn[i + 1, j, k] - vn[i, j, k]) / (dy) +
                                                                (wn[i, j, k + 1] - wn[i, j, k]) / (dz)))) + (
                             e[i, j, k] * lambdaM[i, j + 1, k] + f[i, j, k] * lambdaM1[i, j - 1, k] + Aj * (
                             g[i, j, k] * lambdaM[i + 1, j, k] + h[i, j, k] * lambdaM1[i - 1, j, k]) + Bk * (
                                     m[i, j, k] * lambdaM[i, j, k + 1] + n[i, j, k] * lambdaM1[i, j, k - 1]))) / (
                            2. * (o[i, j, k] + Aj * p[i, j, k] + Bk * q[i, j, k]))) + (1 - omega) * lambdaM1[i, j, k]

            # lambdaM1[i, j, k] = omega * (
            #         ((-1.) * (dx ** 2 * (-2. * alphaH ** 2) * (((un[i, j, k] - un[i, j - 1, k]) / (dx) + (
            #                 vn[i, j, k] - vn[i - 1, j, k]) / (dy) +
            #                                                     (wn[i, j, k] - wn[i, j, k - 1]) / (dz)))) + (
            #                  e[i, j, k] * lambdaM[i, j + 1, k] + f[i, j, k] * lambdaM1[i, j - 1, k] + Aj * (
            #                  g[i, j, k] * lambdaM[i + 1, j, k] + h[i, j, k] * lambdaM1[i - 1, j, k]) + Bk * (
            #                          m[i, j, k] * lambdaM[i, j, k + 1] + n[i, j, k] * lambdaM1[i, j, k - 1]))) / (
            #                 2. * (o[i, j, k] + Aj * p[i, j, k] + Bk * q[i, j, k]))) + (1 - omega) * lambdaM1[i, j, k]


        print(np.sum(np.abs(lambdaM1 - lambdaM)) / np.sum(np.abs(lambdaM1)))
        if np.sum(np.abs(lambdaM1 - lambdaM)) / np.sum(np.abs(lambdaM1)) < 5e-3:
            break
        else:
            lambdaM[0, :, :] = 0.
            lambdaM[:, 0, :] = 0.
            lambdaM[:, :, 0] = 0.
            lambdaM[-1, :, :] = 0.
            lambdaM[:, -1, :] = 0.
            lambdaM[:, :, -1] = 0.
            lambdaM1[0, :, :] = 0.
            lambdaM1[:, 0, :] = 0.
            lambdaM1[:, :, 0] = 0.
            lambdaM1[-1, :, :] = 0.
            lambdaM1[:, -1, :] = 0.
            lambdaM1[:, :, -1] = 0.

            u[:, 1:ny, :] = un[:, 1:ny, :] + 0.5 * (
                    1. / (alphaH ** 2)) * (lambdaM1[:, 1:ny, :] - lambdaM1[:, 0:ny - 1, :]) / dy
            v[1:nx, :, :] = vn[1:nx, :, :] + 0.5 * (
                    1. / (alphaH ** 2)) * (lambdaM1[1:nx, :, :] - lambdaM1[0:nx - 1, :, :]) / dx
            w[:, :, 1:nz] = wn[:, :, 1:nz] + 0.5 * (
                    1. / (alphaV ** 2)) * (lambdaM1[:, :, 1:nz] - lambdaM1[:, :, 0:nz - 1]) / dz

        print("Iteration", index + 1, " out of ", iterations)

    return u, v, w, x, y, z, h, lambdaM1