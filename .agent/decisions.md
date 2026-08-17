# Decisions

## D1: Store MethodInfo by value (not pointer)
- EXP-054: Changed to std::optional<MethodInfo>
- Reason: Theoretical pointer safety + ASAN found actual bug was current_result_ not saved

## D2: Save/restore current_result_ in try_recursive_invoke
- EXP-054: Added saved_current_result
- Reason: ASAN caught SEGV at result.total_instructions_executed++

## D3: Return value propagation via last_invoke_return_
- EXP-055: execute_return stores in last_invoke_return_, try_recursive_invoke copies to return_val
- Reason: Previously ALL recursive invokes returned void

## D4: OBJECT_REF(0) treated as null
- EXP-055: Added to if-nez/if-eqz null checks
- Reason: iget-object on null field returned OBJECT_REF(0) not NULL_REF

## D5: getIntent returns non-null Intent
- EXP-056: Changed from null to singleton Intent
- Reason: Real Android always passes non-null Intent to onCreate

## D6: CollectionShadow rejects null objects
- EXP-056: Return not_handled for object_id=0
- Reason: Don't create fake empty collections for null receivers

## D7: isEmpty on null returns false
- EXP-056: bridge_to_api handler
- Reason: Prevent if-nez from treating void as non-zero
