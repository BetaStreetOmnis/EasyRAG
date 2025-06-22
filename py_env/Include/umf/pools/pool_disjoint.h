// Copyright (C) 2023-2024 Intel Corporation
// Under the Apache License v2.0 with LLVM Exceptions. See LICENSE.TXT.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

#pragma once
#ifdef __cplusplus
extern "C" {
#endif

#include <umf/memory_pool.h>
#include <umf/memory_provider.h>

#define UMF_DISJOINT_POOL_MIN_BUCKET_DEFAULT_SIZE ((size_t)8)

/// @brief Memory limits that can be shared between multiple pool instances,
///        i.e. if multiple pools use the same shared limits, sum of those pools'
///        sizes cannot exceed MaxSize.
typedef struct umf_disjoint_pool_shared_limits_t
    umf_disjoint_pool_shared_limits_t;

/// @brief Create a pool limits struct
/// @param MaxSize specifies hard limit for memory allocated from a provider
/// @return pointer to created pool limits struct
umf_disjoint_pool_shared_limits_t *
umfDisjointPoolSharedLimitsCreate(size_t MaxSize);

/// @brief Destroy previously created pool limits struct
/// @param PoolLimits pointer to a pool limits struct
void umfDisjointPoolSharedLimitsDestroy(
    umf_disjoint_pool_shared_limits_t *PoolLimits);

/// @brief Configuration of Disjoint Pool
typedef struct umf_disjoint_pool_params_t {
    /// Minimum allocation size that will be requested from the system.
    /// By default this is the minimum allocation size of each memory type.
    size_t SlabMinSize;

    /// Allocations up to this limit will be subject to chunking/pooling
    size_t MaxPoolableSize;

    /// When pooling, each bucket will hold a max of 'Capacity' unfreed slabs
    size_t Capacity;

    /// Holds the minimum bucket size valid for allocation of a memory type.
    /// This value must be a power of 2.
    size_t MinBucketSize;

    /// Holds size of the pool managed by the allocator.
    size_t CurPoolSize;

    /// Whether to print pool usage statistics
    int PoolTrace;

    /// Memory limits that can be shared between multitple pool instances,
    /// i.e. if multiple pools use the same SharedLimits sum of those pools'
    /// sizes cannot exceed MaxSize.
    umf_disjoint_pool_shared_limits_t *SharedLimits;

    /// Name used in traces
    const char *Name;
} umf_disjoint_pool_params_t;

umf_memory_pool_ops_t *umfDisjointPoolOps(void);

/// @brief Create default params struct for disjoint pool
static inline umf_disjoint_pool_params_t umfDisjointPoolParamsDefault(void) {
    umf_disjoint_pool_params_t params = {
        0,                                         /* SlabMinSize */
        0,                                         /* MaxPoolableSize */
        0,                                         /* Capacity */
        UMF_DISJOINT_POOL_MIN_BUCKET_DEFAULT_SIZE, /* MinBucketSize */
        0,                                         /* CurPoolSize */
        0,                                         /* PoolTrace */
        NULL,                                      /* SharedLimits */
        "disjoint_pool"                            /* Name */
    };

    return params;
}

#ifdef __cplusplus
}
#endif
