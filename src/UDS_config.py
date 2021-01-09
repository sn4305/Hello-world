import udsoncan
Myconfig  = {
        'exception_on_negative_response'    : False,    
        'exception_on_invalid_response'        : False,
        'exception_on_unexpected_response'    : False,
        'security_algo'                : None,
        'security_algo_params'        : None,
        'tolerate_zero_padding'     : True,
        'ignore_all_zero_dtc'         : True,
        'dtc_snapshot_did_size'     : 2,        # Not specified in standard. 2 bytes matches other services format.
        'server_address_format'        : None,        # 8,16,24,32,40
        'server_memorysize_format'    : None,        # 8,16,24,32,40
        'data_identifiers'             : {0xF190: udsoncan.AsciiCodec(15)},
        'input_output'                 : {},
        'request_timeout'            : 5,
        'p2_timeout'                : 2, 
        'p2_star_timeout'            : 5,
}