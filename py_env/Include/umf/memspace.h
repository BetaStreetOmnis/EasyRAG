/*
 *
 * Copyright (C) 2023 Intel Corporation
 *
 * Under the Apache License v2.0 with LLVM Exceptions. See LICENSE.TXT.
 * SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
 *
 */

#ifndef UMF_MEMSPACE_H
#define UMF_MEMSPACE_H 1

#include <umf/base.h>
#include <umf/memory_pool.h>
#include <umf/memory_provider.h>
#include <umf/mempolicy.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct umf_memspace_t *umf_memspace_handle_t;
typedef const struct umf_memspace_t *umf_const_memspace_handle_t;

///
/// \brief Creates new memory pool from memspace and policy.
/// \param hMemspace handle to memspace
/// \param hPolicy handle to policy
/// \param hPool [out] handle to the newly created memory pool
/// \return UMF_RESULT_SUCCESS on success or appropriate error code on failure.
///
umf_result_t umfPoolCreateFromMemspace(umf_const_memspace_handle_t hMemspace,
                                       umf_const_mempolicy_handle_t hPolicy,
                                       umf_memory_pool_handle_t *hPool);

///
/// \brief Creates new memory provider from memspace and policy.
/// \param hMemspace handle to memspace
/// \param hPolicy handle to policy
/// \param hProvider [out] handle to the newly created memory provider
/// \return UMF_RESULT_SUCCESS on success or appropriate error code on failure.
///
umf_result_t
umfMemoryProviderCreateFromMemspace(umf_const_memspace_handle_t hMemspace,
                                    umf_const_mempolicy_handle_t hPolicy,
                                    umf_memory_provider_handle_t *hProvider);
///
/// \brief Creates new memspace from array of NUMA node ids.
/// \param nodeIds array of NUMA node ids
/// \param numIds size of the array
/// \param hMemspace [out] handle to the newly created memspace
/// \return UMF_RESULT_SUCCESS on success or appropriate error code on failure.
///
umf_result_t umfMemspaceCreateFromNumaArray(unsigned *nodeIds, size_t numIds,
                                            umf_memspace_handle_t *hMemspace);

///
/// \brief Destroys memspace
/// \param hMemspace handle to memspace
///
void umfMemspaceDestroy(umf_memspace_handle_t hMemspace);

///
/// \brief Retrieves predefined host all memspace.
/// \return host all memspace handle on success or NULL on failure.
///
umf_const_memspace_handle_t umfMemspaceHostAllGet(void);

///
/// \brief Retrieves predefined highest capacity memspace.
/// \return highest capacity memspace handle on success or NULL on failure.
///
umf_const_memspace_handle_t umfMemspaceHighestCapacityGet(void);

/// \brief Retrieves predefined highest bandwidth memspace.
/// \return highest bandwidth memspace handle on success or NULL on
///         failure (no HMAT support).
///
umf_const_memspace_handle_t umfMemspaceHighestBandwidthGet(void);

/// \brief Retrieves predefined lowest latency memspace.
/// \return lowest latency memspace handle on success or NULL on
///         failure (no HMAT support).
///
umf_const_memspace_handle_t umfMemspaceLowestLatencyGet(void);

#ifdef __cplusplus
}
#endif

#endif /* UMF_MEMSPACE_H */
