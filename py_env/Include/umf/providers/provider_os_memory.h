/*
 * Copyright (C) 2022-2024 Intel Corporation
 *
 * Under the Apache License v2.0 with LLVM Exceptions. See LICENSE.TXT.
 * SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
*/

#ifndef UMF_OS_MEMORY_PROVIDER_H
#define UMF_OS_MEMORY_PROVIDER_H

#include "umf/memory_provider.h"

#ifdef __cplusplus
extern "C" {
#endif

/// @cond
#define UMF_OS_RESULTS_START_FROM 1000
/// @endcond

/// @brief Protection of the memory allocations
typedef enum umf_mem_protection_flags_t {
    UMF_PROTECTION_NONE = (1 << 0),  ///< Memory allocations can not be accessed
    UMF_PROTECTION_READ = (1 << 1),  ///< Memory allocations can be read.
    UMF_PROTECTION_WRITE = (1 << 2), ///< Memory allocations can be written.
    UMF_PROTECTION_EXEC = (1 << 3),  ///< Memory allocations can be executed.
    /// @cond
    UMF_PROTECTION_MAX // must be the last one
    /// @endcond
} umf_mem_protection_flags_t;

/// @brief Memory visibility mode
typedef enum umf_memory_visibility_t {
    UMF_MEM_MAP_PRIVATE = 1, ///< private memory mapping
    UMF_MEM_MAP_SHARED, ///< shared memory mapping (supported on Linux only)
} umf_memory_visibility_t;

/// @brief Memory binding mode
/// Specifies how memory is bound to NUMA nodes on systems that support NUMA.
/// Not every mode is supported on every system.
typedef enum umf_numa_mode_t {
    /// Default binding mode. Actual binding policy is system-specific. On
    /// linux this corresponds to MPOL_DEFAULT. If this mode is specified,
    /// nodemask must be NULL and maxnode must be 0.
    UMF_NUMA_MODE_DEFAULT,

    /// Restricts memory allocation to nodes specified in nodemask. Allocations
    /// might come from any of the allowed nodes. Nodemask must specify at
    // least one node.
    UMF_NUMA_MODE_BIND,

    /// Interleaves memory allocations across the set of nodes specified in
    /// nodemask. Nodemask must specify at least one node.
    UMF_NUMA_MODE_INTERLEAVE,

    /// Specifies preferred node for allocation. If allocation cannot be
    /// fulfilled, memory will be allocated from other nodes.
    UMF_NUMA_MODE_PREFERRED,

    /// Allocation will be split evenly across nodes specified in nodemask.
    /// umf_numa_split_partition_t can be passed in umf_os_memory_provider_params_t structure
    /// to specify other distribution.
    UMF_NUMA_MODE_SPLIT,
    /// The memory is allocated on the node of the CPU that triggered the
    /// allocation. If this mode is specified, nodemask must be NULL and
    /// maxnode must be 0.
    UMF_NUMA_MODE_LOCAL, // TODO: should this be a hint or strict policy?
} umf_numa_mode_t;

/// @brief This structure specifies a user-defined page distribution
/// within a single allocation in UMF_NUMA_MODE_SPLIT mode.
typedef struct umf_numa_split_partition_t {
    /// The weight of the partition, representing the proportion of
    /// the allocation that should be assigned to this NUMA node.
    unsigned weight;
    /// The NUMA node where the pages assigned to this partition will be bound.
    unsigned target;
} umf_numa_split_partition_t;

/// @brief Memory provider settings struct
typedef struct umf_os_memory_provider_params_t {
    /// Combination of 'umf_mem_protection_flags_t' flags
    unsigned protection;
    /// memory visibility mode
    umf_memory_visibility_t visibility;
    /// (optional) a name of a shared memory file (valid only in case of the shared memory visibility)
    char *shm_name;

    // NUMA config
    /// ordered list of numa nodes
    unsigned *numa_list;
    /// length of numa_list
    unsigned numa_list_len;

    /// Describes how node list is interpreted
    umf_numa_mode_t numa_mode;
    /// part size for interleave mode - 0 means default (system specific)
    /// It might be rounded up because of HW constraints
    size_t part_size;

    /// ordered list of the partitions for the split mode
    umf_numa_split_partition_t *partitions;
    /// len of the partitions array
    unsigned partitions_len;
} umf_os_memory_provider_params_t;

/// @brief OS Memory Provider operation results
typedef enum umf_os_memory_provider_native_error {
    UMF_OS_RESULT_SUCCESS = UMF_OS_RESULTS_START_FROM, ///< Success
    UMF_OS_RESULT_ERROR_ALLOC_FAILED,        ///< Memory allocation failed
    UMF_OS_RESULT_ERROR_ADDRESS_NOT_ALIGNED, ///< Allocated address is not aligned
    UMF_OS_RESULT_ERROR_BIND_FAILED, ///< Binding memory to NUMA node failed
    UMF_OS_RESULT_ERROR_FREE_FAILED, ///< Memory deallocation failed
    UMF_OS_RESULT_ERROR_PURGE_LAZY_FAILED,     ///< Lazy purging failed
    UMF_OS_RESULT_ERROR_PURGE_FORCE_FAILED,    ///< Force purging failed
    UMF_OS_RESULT_ERROR_TOPO_DISCOVERY_FAILED, ///< HWLOC topology discovery failed
} umf_os_memory_provider_native_error_t;

umf_memory_provider_ops_t *umfOsMemoryProviderOps(void);

/// @brief Create default params for os memory provider
static inline umf_os_memory_provider_params_t
umfOsMemoryProviderParamsDefault(void) {
    umf_os_memory_provider_params_t params = {
        UMF_PROTECTION_READ | UMF_PROTECTION_WRITE, /* protection */
        UMF_MEM_MAP_PRIVATE,                        /* visibility mode */
        NULL, /* (optional) a name of a shared memory file (valid only in case of the shared memory visibility) */
        NULL, /* numa_list */
        0,    /* numa_list_len */
        UMF_NUMA_MODE_DEFAULT, /* numa_mode */
        0,                     /* part_size */
        NULL,                  /* partitions */
        0};                    /* partitions_len*/

    return params;
}

#ifdef __cplusplus
}
#endif

#endif /* UMF_OS_MEMORY_PROVIDER_H */
