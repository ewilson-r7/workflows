# Step Type Contract (evidence-based)

Per step `type`, derived from real workflows: how many times it appears, which keys are ALWAYS present, which are sometimes present, and the critical `outputJSONSchema` rule. The `outputJSONSchema` rule is the #1 cause of silent import failures.

## `action`  (plugin_action, 1325 uses)

Plugin action step. Always has plugin{name,slugVendor,slugName,slugVersion,imageData}, identifier (action name), connection, and isCloud. parameters.input mirrors the action's declared input schema.

- **`outputJSONSchema`**: null (an object ONLY for custom-output actions like python_3_script/jq that expose named outputs)
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, identifier, isDisabled, name, nodeId, outputJSONSchema, parameters, plugin, type`
- **Sometimes present**: isCloud (1295), caseManagementInputJsonSchema (369), caseManagementOutputJsonSchema (369)
- Schema-state distribution: `{"defaultInputJSONSchema": {"populated_object": 1325}, "defaultOutputJSONSchema": {"populated_object": 1325}, "outputJSONSchema": {"null": 1300, "populated_object": 25}}`

## `automated_decision`  (native, 617 uses)

Branching by expression. parameters.stepControlParams[] each with edgeId + expression AST + expressionText; plus defaultEdgeId.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (168), caseManagementOutputJsonSchema (168)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 617}, "defaultOutputJSONSchema": {"null": 617}, "outputJSONSchema": {"null": 617}}`

## `artifact`  (native, 609 uses)

Markdown output card. parameters={input:{content:'...markdown...'}, type:'markdown'}. All schema fields null.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (132), caseManagementOutputJsonSchema (132)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 609}, "defaultOutputJSONSchema": {"null": 609}, "outputJSONSchema": {"null": 609}}`

## `action_chatops`  (chatops, 484 uses)

Slack action step (send message / prompt). chatOpsAppName='slack' + chatOpsIdentifier at step root. No plugin object.

- **`outputJSONSchema`**: null
- **Always present keys**: `chatOpsAppName, chatOpsIdentifier, connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (76), caseManagementOutputJsonSchema (76)
- Schema-state distribution: `{"defaultInputJSONSchema": {"populated_object": 484}, "defaultOutputJSONSchema": {"populated_object": 484}, "outputJSONSchema": {"null": 484}}`

## `trigger`  (native_or_plugin_trigger, 234 uses)

The workflow's single entry point. Has triggerId matching the kom.triggers[] entry UUID. Plugin triggers add plugin+identifier+connection; Slack adds chatOpsAppName/chatOpsIdentifier; native API/scheduled triggers have neither.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, triggerId, type`
- **Sometimes present**: parameters (175), identifier (103), plugin (91), chatOpsAppName (82), chatOpsIdentifier (82), caseManagementInputJsonSchema (58), caseManagementOutputJsonSchema (58), description (53)
- Schema-state distribution: `{"defaultInputJSONSchema": {"populated_object": 231, "empty_object": 3}, "defaultOutputJSONSchema": {"populated_object": 231, "empty_object": 3}, "outputJSONSchema": {"null": 231, "empty_object": 3}}`

## `loop`  (native, 233 uses)

Iterates a body subgraph. parameters has innerEdgeId, nextEdgeId, repeatCount/repeatDelay or a collection; carries an outputJSONSchema object.

- **`outputJSONSchema`**: object ALWAYS (empty or populated with customOutput vars) - NEVER null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (67), caseManagementOutputJsonSchema (67)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 233}, "defaultOutputJSONSchema": {"null": 233}, "outputJSONSchema": {"empty_object": 174, "populated_object": 58, "null": 1}}`

## `join`  (native, 85 uses)

Waits for parallel branches to converge; carries an outputJSONSchema object (and defaultOutputJSONSchema).

- **`outputJSONSchema`**: object ALWAYS (empty {properties:{},title:Variables,type:object} or populated) - NEVER null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (26), caseManagementOutputJsonSchema (26)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 85}, "defaultOutputJSONSchema": {"populated_object": 38, "empty_object": 47}, "outputJSONSchema": {"populated_object": 38, "empty_object": 47}}`

## `pattern_match`  (native, 84 uses)

Regex/variable extraction. parameters has expressions[], expressionText, input, captureAll, ignoreCase.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (17), caseManagementOutputJsonSchema (17)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 84}, "defaultOutputJSONSchema": {"null": 84}, "outputJSONSchema": {"null": 84}}`

## `break`  (native, 27 uses)

Breaks out of an enclosing loop. Standard native step keys, no special params.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (16), caseManagementOutputJsonSchema (16)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 27}, "defaultOutputJSONSchema": {"null": 27}, "outputJSONSchema": {"null": 27}}`

## `decision_chatops`  (chatops, 25 uses)

Slack interactive decision (buttons). chatOpsAppName='slack' + chatOpsIdentifier.

- **`outputJSONSchema`**: null
- **Always present keys**: `chatOpsAppName, chatOpsIdentifier, connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- Schema-state distribution: `{"defaultInputJSONSchema": {"populated_object": 25}, "defaultOutputJSONSchema": {"populated_object": 25}, "outputJSONSchema": {"null": 25}}`

## `filter`  (native, 20 uses)

Single-condition gate. parameters has stepControlParam (singular) + stopOnMatch.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (11), caseManagementOutputJsonSchema (11)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 20}, "defaultOutputJSONSchema": {"null": 20}, "outputJSONSchema": {"null": 20}}`

## `helpers`  (native, 14 uses)

Global artifact / helper step. Adds helperIdentifier and (usually) globalArtifact keys.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, helperIdentifier, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: globalArtifact (13), caseManagementInputJsonSchema (8), caseManagementOutputJsonSchema (8)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 14}, "defaultOutputJSONSchema": {"null": 14}, "outputJSONSchema": {"null": 14}}`

## `human_decision`  (native, 7 uses)

Waits for a human choice. parameters has defaultEdgeId, notifications, stepControlParams[], timeout, timeoutDisplayUnit, timeoutEdgeId.

- **`outputJSONSchema`**: null
- **Always present keys**: `connectionType, continueOnFailure, defaultImageData, defaultInputJSONSchema, defaultOutputJSONSchema, isDisabled, name, nodeId, outputJSONSchema, parameters, type`
- **Sometimes present**: caseManagementInputJsonSchema (3), caseManagementOutputJsonSchema (3)
- Schema-state distribution: `{"defaultInputJSONSchema": {"null": 7}, "defaultOutputJSONSchema": {"null": 7}, "outputJSONSchema": {"null": 7}}`
