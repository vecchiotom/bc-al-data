# AL diagnostic map — summary

Total codes mapped: **1324**  (919 AL compiler + 405 analyzer rules)

Severity: error 827, warning 398, info 99

Hallucination likelihood: high 116, medium 499, low 393, none 316

## By category

### analyzer-correctness  (124 codes, 0 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AC0000 | info | Analyzer '{0}' threw an exception of type '{1}': {2} | low | model |
| AC0001 | info | Table '{0}' is used in list page '{1}' but does not define b | low | model |
| AC0002 | warning | NotBlank property should be set explicitly for tables with a | low | model |
| AC0003 | warning | The NotBlank property should be set to false (or removed) if | low | model |
| AC0004 | info | Confirm() must be implemented through the "Confirm Managemen | low | model |
| AC0005 | info | GlobalLanguage() must be implemented through the "Translatio | low | model |
| AC0006 | warning | Invoke pages through the "Page Management" codeunit instead  | low | model |
| AC0007 | warning | Set Access property to Internal for Install and Upgrade code | low | model |
| AC0008 | info | The table object does not explicitly define the DataPerCompa | low | model |
| AC0009 | warning | The Caption of permissionset objects should not exceed {0} c | low | model |
| AC0010 | warning | The application object {0} '{1}' is not covered by any Permi | low | model |
| AC0011 | info | A user-facing object or control is missing a Caption. | low | model |
| AC0012 | warning | Integration event '{0}' is declared in a codeunit with Acces | low | model |
| AC0013 | info | Table '{0}' is missing the required '{1}' fieldgroup. | low | model |
| AC0014 | info | ToolTip must end with one of the following punctuations: '{0 | low | model |
| AC0015 | info | ToolTip should start with the verb 'Specifies'. | low | model |
| AC0016 | info | ToolTip text must not contain line breaks. | low | model |
| AC0017 | info | ToolTip exceeds the recommended maximum length of 200 charac | low | model |
| AC0018 | warning | The Caption property is empty but not locked. Empty captions | low | model |
| AC0019 | info | Enum value '{0}' with ordinal 0 should have an empty Name an | low | model |
| AC0020 | warning | Label '{0}' is suffixed with 'Tok' but does not have the Loc | medium | analyzer-codefix |
| AC0021 | info | Label '{0}' has the Locked property set to true but is not s | medium | analyzer-codefix |
| AC0022 | warning | The empty enum value defines a Caption, which will never be  | low | model |
| AC0023 | warning | The enum value '{0}' has an empty Caption and will not be sh | low | model |
| AC0024 | warning | Event publisher method '{0}' should be declared as local or  | low | model |
| AC0025 | info | Use the (CR)LFSeparator from the "Type Helper" codeunit from | low | model |
| AC0026 | info | Field '{0}' is not exposed on any page and should explicitly | low | model |
| AC0027 | info | Label '{0}' represents a token but does not use the required | medium | analyzer-codefix |
| AC0028 | info | A value for the ToolTip property is missing for the table fi | low | model |
| AC0029 | info | The ToolTip property of page field '{0}'' and it's table fie | low | model |
| AC0030 | info | The return value of the '{0}' method must be used to improve | low | model |
| AC0031 | info | The object does not declare permission '{0}' for tabledata ' | low | model |
| AC0032 | info | Permission 'tabledata {0}' is declared but this object perfo | low | model |
| AW0001 | warning | The Web client does not support displaying the Request page  | low | model |
| AW0002 | warning | The Web client does not support displaying both Actions and  | low | model |
| AW0003 | warning | The Web client does not support displaying Repeater controls | low | model |
| AW0004 | warning | A Blob cannot be used as a source expression for a page fiel | low | model |
| AW0005 | info | Action with name '{0}' should have a value for the Image pro | low | model |
| AW0006 | info | The {0} '{1}' should use the UsageCategory and ApplicationAr | low | model |
| AW0007 | error | The FlowFilter field '{0}' in the Repeater control '{1}' can | low | model |
| AW0008 | warning | The repeater '{0}' in page '{1}' is not supported by the Web | low | model |
| AW0009 | warning | Using a Blob with subtype Bitmap on a page field is deprecat | low | model |
| AW0010 | warning | A Repeater control used on a List page must be defined at th | low | model |
| AW0011 | info | Group "{0}" only contains promoted actions that are not set  | low | model |
| AW0012 | warning | The '{0}' property cannot be declared on '{1}' of type '{2}' | low | model |
| AW0013 | warning | The group '{0}' defined in {1} '{2}' should not be hidden be | low | model |
| AW0014 | warning | The group '{0}' defined in {1} '{2}' should not be hidden be | low | model |
| AW0015 | warning | The action '{0}' defined in {1} '{2}' is marked with 'Scope  | low | model |
| AW0016 | warning | The Rich Text Editor field '{0}' defined in {1} '{2}' should | low | model |
| AW0017 | warning | The MaskType property cannot be used inside repeater control | low | model |
| LC0000 | info | Analyzer '{0}' threw an exception of type '{1}': {2} | low | model |
| LC0003 | warning | Object ID '{0}' used as object reference. Use the object nam | low | model |
| LC0007 | info | Maintainability index: {0} (threshold ≤ {1}) | low | model |
| LC0008 | warning | Maintainability index: {0} (threshold ≤ {1}) | low | model |
| LC0009 | info | Cyclomatic complexity: {0} (threshold ≥ {1}) | low | model |
| LC0010 | warning | Cyclomatic complexity: {0} (threshold ≥ {1}) | low | model |
| LC0019 | warning | DataClassification matches the table-level DataClassificatio | low | model |
| LC0020 | warning | ApplicationArea matches the page-level ApplicationArea and c | low | model |
| LC0028 | warning | Event subscriber arguments should use identifier syntax inst | low | model |
| LC0031 | info | Use ReadIsolation(IsolationLevel::UpdLock) instead of LockTa | low | model |
| LC0033 | warning | The specified runtime version in app.json is falling behind. | low | model |
| LC0040 | warning | The method call '{0}' does not explicitly specify the RunTri | low | model |
| LC0043 | warning | Sensitive textual values should be passed as SecretText to p | low | model |
| LC0048 | warning | Error is called with a Text value. Use ErrorInfo or a Label  | low | model |
| LC0052 | warning | The {0} method {1} in {2} {3} (Access = {4}) is declared but | low | model |
| LC0053 | warning | The {0} method {1} is only used in the object {2} {3} (Acces | low | model |
| LC0054 | warning | Interface '{0}' must start with a capital 'I' and must not c | medium | analyzer-codefix |
| LC0063 | info | Consider naming field with a more descriptive name: '{0}'. | low | model |
| LC0081 | warning | Avoid using {0}.Count() for checking record existence. Use { | low | analyzer-codefix |
| LC0082 | info | Consider using a Query object or {0}.Find('-') together with | low | analyzer-codefix |
| LC0083 | warning | Use the new method {0}.{1} to extract specific parts of date | low | model |
| LC0086 | warning | Avoid using the string literal '{0}' for page styling. Use t | low | analyzer-codefix |
| LC0088 | info | Prefer using an Enum instead of an Option type. | low | analyzer-codefix |
| LC0089 | info | Cognitive Complexity: {0} (threshold ≥ {1}) | low | model |
| LC0089i | info |  | low | analyzer-codefix |
| LC0090 | warning | Cognitive Complexity: {0} (threshold ≥ {1}) | low | model |
| LC0091 | warning | Missing translation for '{0}' in language(s): {1} | low | model |
| LC0092 | warning | {0} name "{1}" {2} | low | model |
| LC0094 | warning | AllowInCustomizations matches the table-level AllowInCustomi | low | model |
| LC0095 | warning | Parameter '{0}' is not referenced in procedure '{1}'. | low | model |
| LC0096 | warning | The record variable '{0}' is passed as an argument to a meth | low | model |
| LC0097 | info | {0} '{1}' mixes exit() with assignments to the named return  | low | model |
| LC0098 | info | Event subscriber '{0}' does not match the expected name '{1} | low | model |
| LC0099 | info | Parameter '{0}' is not referenced in event subscriber '{1}'. | low | model |
| PC0000 | info | Analyzer '{0}' threw an exception of type '{1}': {2} | low | model |
| PC0001 | warning | Field '{0}' is editable, which is uncommon for a FlowField.  | low | model |
| PC0002 | error | AutoIncrement is used in a table with TableType = Temporary, | low | model |
| PC0003 | error | SetRange is called with a filter expression. Use SetFilter i | low | model |
| PC0004 | error | List objects are 1-based | low | model |
| PC0005 | warning | The property Extensible should be explicitly set for public  | low | model |
| PC0006 | warning | {0} '{1}' does not explicitly have the Access property set. | low | model |
| PC0007 | error | The AutoCalcFields method should only be used with FlowField | low | analyzer-codefix |
| PC0008 | error | Found operator '{0}' together with placeholder '{1}' in filt | low | model |
| PC0010 | warning | Parameter '{0}' must use the 'var' keyword if the publisher  | low | model |
| PC0011 | warning | Parameter '{0}' must use the 'var' keyword if the publisher  | low | model |
| PC0012 | warning | Direct assignment to the '{0}' field of type FlowFilter inva | low | analyzer-codefix |
| PC0013 | error | Invalid arguments in call to '{0}' for record '{1}': {2}. | low | model |
| PC0014 | warning | Double quote character detected in JPath expression. Replace | low | model |
| PC0015 | error | Use 'IsNullGuid({0})' method instead of comparing the GUID ' | low | model |
| PC0016 | warning | Clear(All) does not affect or change values for global varia | low | model |
| PC0017 | warning | Argument {0}: cannot convert from {1} to {2}. | low | model |
| PC0018 | error | SourceTable property is not defined on Page '{0}'. Method '{ | low | model |
| PC0019 | warning | Filter string {0} uses incorrect single-quote escaping for a | low | model |
| PC0020 | warning | Fields {5} and {6} with ID {0} have a possible incompatible  | low | model |
| PC0021 | warning | Field with ID {0} resolves to different field names ({3} ≠ { | low | model |
| PC0022 | warning | Possible overflow assigning '{0}' to '{1}'. | low | model |
| PC0023 | warning | Do not set the 'IsHandled' parameter to 'false' or any value | low | model |
| PC0024 | info | The 'ApplicationArea' property is not applicable to API page | low | model |
| PC0025 | error | The ODataKeyFields property is set to '{0}', but should use  | low | model |
| PC0026 | warning | "Field 'Rec.{0}' exposed with the name '{1}' should always b | low | model |
| PC0027 | warning | Do not execute table triggers or validation methods on tempo | low | model |
| PC0028 | warning | The related field has length {0} ({1}) which is longer than  | low | model |
| PC0029 | info | Use 'CreateSequentialGuid()' instead of '{0}'. {1} | low | model |
| PC0030 | info | Use SetLoadFields before '{0}.{1}()' to improve performance  | low | model |
| PC0031 | warning | Do not use '{0}' before full-field operations ({1}) on '{2}' | low | model |
| PC0032 | error | Report layout {0} is {1} characters long, but the maximum is | low | model |
| PC0033 | warning | Control '{0}' has a duplicate OData EntityName '{1}'. This w | low | analyzer-codefix |
| PC0034 | warning | The format string contains {0} placeholder(s), but {1} argum | low | model |
| PC0035 | warning | Move CalcFields to SetAutoCalcFields before the loop on '{0} | low | model |
| PC0036 | warning | {0}.SetRecord(): You cannot use a temporary record for the R | low | model |
| PC0037 | warning | Use Validate() instead of direct field assignment on '{0}'. | low | model |
| PC0038 | info | '{0}': not all code paths return a value | low | model |
| TA0000 | info | Analyzer '{0}' threw an exception of type '{1}': {2} | low | model |
| TA0001 | info | Global procedure '{0}' declared in a test codeunit without a | low | model |

### analyzer-style  (112 codes, 0 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AA0001 | warning | There must be exactly one space character on each side of '{ | medium | analyzer-codefix |
| AA0002 | warning | There must be no space character after '{0}'. | medium | analyzer-codefix |
| AA0003 | warning | There must be exactly one space character after '{0}'. | medium | analyzer-codefix |
| AA0005 | warning | Only use BEGIN..END to enclose compound statements. | medium | analyzer-codefix |
| AA0008 | warning | You must specify open and close parenthesis after '{0}'. | medium | analyzer-codefix |
| AA0013 | warning | When BEGIN follows THEN, ELSE, DO, it should be on the same  | medium | analyzer-codefix |
| AA0018 | warning | The '{0}' keyword should always start a line. | low | analyzer-codefix |
| AA0021 | warning | Variable declarations should be ordered by type. Variables s | medium | analyzer-codefix |
| AA0022 | warning | Substitute the IF THEN ELSE structure with a CASE. | low | analyzer-codefix |
| AA0040 | warning | This WITH statement is nested inside another WITH statement  | low | analyzer-codefix |
| AA0050 | warning | Permissions for the object '{0}' should not be added through | low | analyzer-codefix |
| AA0051 | warning | The permission set '{0}' should not be included through a pe | low | analyzer-codefix |
| AA0052 | warning | The permission set '{0}' should not be included through a pe | low | analyzer-codefix |
| AA0053 | warning | Wildcard permissions should not be included in a permission  | low | analyzer-codefix |
| AA0072 | info | The name of {0} is not valid. The name of variables and para | medium | analyzer-codefix |
| AA0073 | warning | The name of temporary variable '{0}' must be prefixed with T | medium | analyzer-codefix |
| AA0074 | warning | Variable '{0}' must have a suffix from this list: Msg, Tok,  | medium | analyzer-codefix |
| AA0087 | warning | Do only lower permissions inside procedures of type test. | low | analyzer-codefix |
| AA0100 | warning | Do not have identifiers with quotes in the name. | low | analyzer-codefix |
| AA0101 | warning | For pages of the type API the value of properties APIPublish | low | analyzer-codefix |
| AA0102 | warning | Field controls in pages of type API should have a camel case | low | analyzer-codefix |
| AA0103 | warning | For queries of the type API the value of properties APIPubli | low | analyzer-codefix |
| AA0104 | warning | Column controls in queries of type API should have a camel c | low | analyzer-codefix |
| AA0105 | error | PagePart controls must not refer to parent pages. | low | analyzer-codefix |
| AA0106 | error | A page of type API can only refer to the same subpage once. | low | analyzer-codefix |
| AA0131 | warning | The number of parameters passed to a string must match the p | low | analyzer-codefix |
| AA0136 | warning | Unreachable code detected. | low | analyzer-codefix |
| AA0137 | warning | Variable '{0}' is unused in '{1}'. | low | analyzer-codefix |
| AA0139 | warning | Possible overflow assigning '{0}' to '{1}'. | low | analyzer-codefix |
| AA0150 | warning | Parameter '{0}' is declared by reference but never changed i | low | analyzer-codefix |
| AA0161 | warning | Only use AssertError in Test Codeunits. | low | analyzer-codefix |
| AA0175 | warning | Variable '{0}' queries the database in '{1}' but does not us | low | analyzer-codefix |
| AA0181 | warning | The FindSet() or Find() method on the record '{0}' must be u | low | analyzer-codefix |
| AA0189 | warning | Value '{0}' found on control {1} {2}. Valid values are {3}. | low | analyzer-codefix |
| AA0194 | warning | Remember to specify either the 'OnAction' trigger or the 'Ru | low | analyzer-codefix |
| AA0198 | warning | The name of the local variable '{0}' is identical to a globa | low | analyzer-codefix |
| AA0199 | warning | Value '{0}' found on control {1} {2}. Incorrect order, expec | low | analyzer-codefix |
| AA0200 | warning | Value '{0}' found on control {1} {2}. When ApplicationArea i | low | analyzer-codefix |
| AA0201 | warning | Value '{0}' found on control {1} {2}. When ApplicationArea i | low | analyzer-codefix |
| AA0202 | warning | The name of the local variable '{0}' is identical to a field | low | analyzer-codefix |
| AA0203 | warning | The name of the method '{0}' is identical to a field or acti | low | analyzer-codefix |
| AA0204 | warning | The name of the global variable '{0}' is identical to a fiel | low | analyzer-codefix |
| AA0205 | warning | Use of unassigned variable '{0}'. | low | analyzer-codefix |
| AA0206 | warning | The variable '{0}' is initialized but not used. | low | analyzer-codefix |
| AA0207 | warning | The EventSubscriber method {0} must be local. | low | analyzer-codefix |
| AA0210 | info | The table {0} does not contain a key with the field {1}. | low | analyzer-codefix |
| AA0211 | warning | The CalcFields method should only be used with FlowFields or | low | analyzer-codefix |
| AA0213 | warning | The {0} {1} must have specified ObsoleteState and ObsoleteRe | low | analyzer-codefix |
| AA0214 | warning | The record {0} should be modified before saving to the datab | low | analyzer-codefix |
| AA0215 | warning | The file {0} has an incorrect name. The valid name is {1}. | low | analyzer-codefix |
| AA0216 | warning | Use a text constant for passing user messages and errors wit | low | analyzer-codefix |
| AA0217 | warning | Use a text constant or label for format string in StrSubstNo | low | analyzer-codefix |
| AA0218 | warning | The Tooltip property for {0} {1} must be filled. | low | analyzer-codefix |
| AA0219 | info | The Tooltip property for {0} {1} should start with 'Specifie | low | analyzer-codefix |
| AA0220 | warning | The value of the {0} Tooltip property for {1} {2} must be fi | low | analyzer-codefix |
| AA0221 | warning | The OptionCaption property for {0} {1} must be filled in. | low | analyzer-codefix |
| AA0222 | warning | SIFT index should not be used on key {0}. | low | analyzer-codefix |
| AA0223 | warning | The value of the {0} OptionCaption property for {1} {2} must | low | analyzer-codefix |
| AA0224 | warning | The count of option captions specified in the OptionCaption  | low | analyzer-codefix |
| AA0225 | warning | The Caption property for {0} {1} must be filled in. | low | analyzer-codefix |
| AA0226 | warning | The value of the {0} Caption property for {1} {2} must be fi | low | analyzer-codefix |
| AA0227 | warning | Optional return value of the method should not be omitted in | low | analyzer-codefix |
| AA0228 | warning | The local method '{0}' is declared but never used. | low | analyzer-codefix |
| AA0230 | warning | Version should not be specified for internal assembly '{0}'. | low | analyzer-codefix |
| AA0231 | warning | Do not use the StrSubstNo or string concatenation as a param | low | analyzer-codefix |
| AA0232 | info | The FlowField {0} of {1} should be added to the SIFT key. | low | analyzer-codefix |
| AA0233 | warning | The '{0}' method on the record '{1}' must be used without th | low | analyzer-codefix |
| AA0234 | info | The Tooltip property for {0} {1} should be filled in. | low | analyzer-codefix |
| AA0235 | info | Codeunit '{0}' should contain the 'Company-Initialize'::'OnC | low | analyzer-codefix |
| AA0237 | warning | The name of non temporary variables '{0}' must not be prefix | medium | analyzer-codefix |
| AA0240 | warning | The {0} '{1}' must not contain email addresses or phone numb | low | analyzer-codefix |
| AA0241 | info | You must use all lowercase letters for reserved keyword '{0} | medium | analyzer-codefix |
| AA0242 | warning | Field '{0}' is not selected for loading and accessing it may | low | analyzer-codefix |
| AA0243 | warning | Running a codeunit of subtype upgrade is not allowed. | low | analyzer-codefix |
| AA0244 | warning | The name of the parameter '{0}' is identical to a global var | low | analyzer-codefix |
| AA0245 | warning | The name of the parameter '{0}' is identical to a field, met | low | analyzer-codefix |
| AA0246 | warning | Suppressing all diagnostics is not allowed. Specify the diag | low | analyzer-codefix |
| AA0247 | info | Use namespaces to organize your code and isolate it from cha | medium | analyzer-codefix |
| AA0248 | info | Add 'this' qualification. | low | analyzer-codefix |
| AA0249 | warning | Trigger {0} of PageField {1} is never invoked from the UI du | low | analyzer-codefix |
| AA0250 | warning | The {0} '{1}' is marked for obsoletion. Consider explicitly  | low | analyzer-codefix |
| AA0251 | error | The external business event '{0}' is marked for obsoletion.  | low | analyzer-codefix |
| AA0252 | error | Moving the external business event '{0}' to another app is n | low | analyzer-codefix |
| AA0448 | warning | Use FieldCaption instead of FieldName and TableCaption inste | low | analyzer-codefix |
| AA0462 | warning | The CalcDate should only be used with DataFormula variables. | low | analyzer-codefix |
| AA0470 | warning | Variable '{0}' with placeholders should have a comment expla | low | analyzer-codefix |
| AA0471 | info | The AutoFormatType property for {0} {1} defined in {2} '{3}' | low | analyzer-codefix |
| AA0472 | info | The AutoFormatExpression property for {0} {1} defined in {2} | low | analyzer-codefix |
| AA0473 | info | The AutoFormatType property for {0} {1} defined in {2} '{3}' | low | analyzer-codefix |
| AA0474 | info | The AutoFormatExpression property for {0} {1} defined in {2} | low | analyzer-codefix |
| AA0475 | error | The Truncate method cannot be used in this context. | low | analyzer-codefix |
| AA0476 | error | The AI test configuration is not valid. {0}. | low | analyzer-codefix |
| AA0477 | info | The using statements are not in a sorted order. | medium | analyzer-codefix |
| DC0000 | info | Analyzer '{0}' threw an exception of type '{1}': {2} | low | analyzer-codefix |
| DC0001 | info | Commit() needs a comment to justify its existence. Add a lea | low | analyzer-codefix |
| DC0002 | info | Writing to a FlowField is not common and requires a comment  | low | analyzer-codefix |
| DC0003 | info | Empty statements should be removed or have a leading or trai | low | analyzer-codefix |
| DC0004 | info | Public procedure '{0}' must include XML documentation commen | low | analyzer-codefix |
| DC0005 | info | The XML documentation does not match the procedure signature | low | analyzer-codefix |
| DC0006 | info | Internal procedure '{0}' must include XML documentation comm | low | analyzer-codefix |
| DC0007 | info | Public object '{0}' must include XML documentation comments. | low | analyzer-codefix |
| DC0008 | info | Internal object '{0}' must include XML documentation comment | low | analyzer-codefix |
| DC0009 | info | Event '{0}' must include XML documentation comments. | low | analyzer-codefix |
| DC0010 | info | Internal event '{0}' must include XML documentation comments | low | analyzer-codefix |
| FC0000 | info | Analyzer '{0}' threw an exception of type '{1}': {2} | low | analyzer-codefix |
| FC0001 | warning | The {0} declaration ends with a semicolon. Remove the traili | medium | analyzer-codefix |
| FC0002 | info | Use '{0}' instead of '{1}' for consistent casing. | medium | analyzer-codefix |
| FC0003 | warning | You must specify open and close parenthesis after '{0}'. | medium | analyzer-codefix |
| FC0004 | info | The Permissions property entries are not ordered alphabetica | low | analyzer-codefix |
| FC0005 | warning | Call method '{0}' using parenthesis instead of assignment sy | medium | analyzer-codefix |
| FC0006 | info | The Permissions property contains uppercase permission value | medium | analyzer-codefix |
| FC0007 | info | Statement blocks should be separated. Insert a blank line {0 | medium | analyzer-codefix |

### binding  (46 codes, 44 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0118 | error | ERR_NameNotInContext | high | model |
| AL0132 | error | ERR_NoSuchMember | high | model |
| AL0134 | error | ERR_UnknownType | high | model |
| AL0162 | error | ERR_UnknownTrigger | high | model |
| AL0167 | error | ERR_MissingAssociatedPropertyMultipleValues | high | model |
| AL0168 | error | ERR_MissingAssociatedProperty | high | model |
| AL0196 | error | ERR_AmbigCall | medium | model |
| AL0223 | error | ERR_MissingAssociatedPropertySingleValue | high | model |
| AL0247 | error | ERR_ExtensionTargetNotFound | high | model |
| AL0270 | error | ERR_ControlNotFound | high | model |
| AL0271 | error | ERR_ActionNotFound | high | model |
| AL0280 | error | ERR_EventNotFound | high | model |
| AL0295 | error | ERR_FieldNotFound | high | model |
| AL0341 | error | ERR_MissingObjectProperty | medium | model |
| AL0383 | error | ERR_UndefinedOptionValue | high | model |
| AL0417 | error | ERR_ControlAddInNotFound | high | model |
| AL0462 | error | ERR_UnknownDotNetEvent | high | model |
| AL0476 | error | ERR_TriggerMissingAssociatedProperty | high | model |
| AL0477 | error | ERR_TriggerMissingAssociatedPropertySingleValue | high | model |
| AL0478 | error | ERR_TriggerMissingAssociatedPropertyMultipleValues | high | model |
| AL0503 | error | ERR_AmbigMemberReference | high | model |
| AL0513 | error | ERR_FieldGroupNotFound | high | model |
| AL0533 | error | ERR_ViewNotFound | high | model |
| AL0670 | error | ERR_ObjectChangeNotFoundInCompilation | high | model |
| AL0681 | error | ERR_DataItemNotFound | high | model |
| AL0682 | error | ERR_DataItemOrColumnNotFound | high | model |
| AL0720 | error | ERR_AppObjectNotFound | high | model |
| AL0727 | warning | WRN_ERR_MissingAssociatedProperty | high | model |
| AL0728 | warning | WRN_ERR_MissingAssociatedPropertySingleValue | high | model |
| AL0729 | warning | WRN_ERR_MissingAssociatedPropertyMultipleValues | high | model |
| AL0731 | warning | WRN_ERR_NameNotInContext | high | model |
| AL0791 | error | ERR_NamespaceNotFound | high | deterministic |
| AL0847 | error | ERR_ThisHaveNoSuchMember | high | model |
| AL0899 | error | ERR_AnalysisViewNotFound | high | model |
| AL0928 | error | ERR_SystemObjectNotFound | high | model |
| AL1404 | warning | WRN_PERS_ActionNotFound | high | model |
| AL1405 | warning | WRN_PERS_ControlNotFound | high | model |
| AL1406 | warning | WRN_PERS_ViewNotFound | high | model |
| AL1410 | warning | WRN_PERS_ExtensionTargetNotFound | high | model |
| AL1418 | warning | WRN_PERS_DataItemNotFound | high | model |
| AL1419 | warning | WRN_PERS_DataItemOrColumnNotFound | high | model |
| AL1422 | warning | WRN_PERS_ActionTargetNotFound | high | model |
| AL1423 | warning | WRN_PERS_NoSuchMember | high | model |
| AL1424 | warning | WRN_PERS_NameNotInContext | high | model |
| AL1426 | warning | WRN_PERS_NamespaceNotFound | high | model |
| AL1428 | warning | WRN_PERS_AnalysisViewNotFound | high | model |

### lexical  (9 codes, 0 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0100 | error | ERR_InvalidMultilineComment | medium | deterministic |
| AL0101 | error | ERR_InvalidDecimalLiteral | medium | deterministic |
| AL0102 | error | ERR_InvalidInt64Literal | medium | deterministic |
| AL0103 | error | ERR_InvalidInt32Literal | medium | deterministic |
| AL0190 | error | ERR_InvalidTimeLiteral | medium | deterministic |
| AL0191 | error | ERR_InvalidDateLiteral | medium | deterministic |
| AL0257 | error | ERR_InvalidDateTimeLiteral | medium | deterministic |
| AL0488 | error | ERR_InvalidControlAddInNameCharacter | medium | deterministic |
| AL0586 | warning | WRN_ERR_IdentifierContainsInvalidCharacters | medium | deterministic |

### metadata  (316 codes, 1 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0119 | error | ERR_DuplicateParamName | none | none |
| AL0121 | error | ERR_DuplicateVariableName | none | none |
| AL0123 | error | ERR_DuplicateReturnValueName | none | none |
| AL0152 | error | ERR_DuplicateOption | none | none |
| AL0155 | error | ERR_DuplicateMemberName | none | none |
| AL0164 | error | ERR_DuplicateTrigger | none | none |
| AL0177 | error | ERR_InvalidApplicationObjectIdentifier | none | none |
| AL0197 | error | ERR_AppObjDuplicateName | none | none |
| AL0206 | error | ERR_DuplicateFieldId | none | none |
| AL0210 | error | ERR_DuplicateControlId | none | none |
| AL0212 | error | ERR_DuplicateAreaKind | none | none |
| AL0222 | error | ERR_InvalidSymbolId | none | none |
| AL0227 | error | ERR_DuplicateKeyId | none | none |
| AL0228 | error | ERR_DuplicateFieldGroupId | none | none |
| AL0231 | error | ERR_DuplicateMemberId | none | none |
| AL0234 | error | ERR_DuplicateActionId | none | none |
| AL0239 | error | ERR_DuplicateAttribute | none | none |
| AL0260 | error | ERR_PrimaryKeyAppendedToSecondaryKey | none | none |
| AL0261 | error | ERR_DuplicateListMember | none | none |
| AL0263 | error | ERR_PrimaryKeyMustBeEnabled | none | none |
| AL0264 | error | ERR_AppObjDuplicateId | none | none |
| AL0275 | error | ERR_AmbigSymbolReference | medium | model |
| AL0296 | error | ERR_SymbolCannotBeUsedInThisContext | none | none |
| AL0297 | error | ERR_ApplicationObjectIdentifierOutOfBounds | none | none |
| AL0303 | error | ERR_AttributeNotOnAValidSymbol | none | none |
| AL0305 | error | ERR_ObjectIdentifierTooLong | none | none |
| AL0308 | error | ERR_PrimaryKeyMustHaveMaintainSqlIndexEnabled | none | none |
| AL0317 | error | ERR_DuplicateProperty | high | deterministic |
| AL0350 | error | ERR_DuplicateColumnReference | none | none |
| AL0380 | error | ERR_CannotMoveSymbolsBetweenAreas | none | none |
| AL0381 | error | ERR_DuplicatedKeyFields | none | none |
| AL0384 | error | ERR_DuplicateColumnOrLabelName | none | none |
| AL0386 | error | ERR_MissingPackageDependency | none | none |
| AL0387 | error | ERR_DuplicateNamespacePrefix | none | none |
| AL0395 | error | ERR_CannotHaveAddSymbolsOnPageCustomizationLayout | none | none |
| AL0402 | error | ERR_DuplicateCaseStatement | none | none |
| AL0411 | error | ERR_DuplicateLabelProperty | none | none |
| AL0426 | error | ERR_DuplicateApiVersionId | none | none |
| AL0449 | error | ERR_DuplicateDotNetTypeAlias | none | none |
| AL0464 | error | ERR_CouldNotDetermineDefaultPrimaryKey | none | none |
| AL0479 | warning | WRN_DuplicateTranslationItemForSameId | none | none |
| AL0486 | warning | WRN_ERR_DuplicateMemberName | none | none |
| AL0495 | error | ERR_DuplicateMemberIdFromHash | none | none |
| AL0512 | error | ERR_MissingSupportedLocalesManifestProperty | none | none |
| AL0514 | error | ERR_DuplicateLegacyEnumId | none | none |
| AL0515 | error | ERR_DuplicateLegacyEnumName | none | none |
| AL0516 | error | ERR_DuplicateLegacyEnumValuesDiffer | none | none |
| AL0518 | error | ERR_DuplicateHandlerMethodName | none | none |
| AL0521 | error | ERR_PrimaryKeyMustNotHaveUnique | none | none |
| AL0524 | warning | WRN_ERR_MethodAlreadyDeclaredInBase | none | none |
| AL0539 | error | ERR_DuplicateTableFieldReference | none | none |
| AL0543 | error | ERR_ContextSentiveHelpRequiresManifestProperty | none | none |
| AL0548 | warning | WRN_ERR_CannotMoveSymbolsBetweenAreas | none | none |
| AL0554 | error | ERR_CannotHaveAddSymbolsOnPageCustomizationActions | none | none |
| AL0565 | error | ERR_InvalidManifestRadCheck | none | none |
| AL0566 | error | ERR_TableUsingReservedFieldId | none | none |
| AL0587 | error | ERR_DuplicateInterfaceImplementationNotAllowed | none | none |
| AL0589 | warning | WRN_ERR_DuplicateColumnDataItemName | none | none |
| AL0599 | error | ERR_ControlAddInDuplicatedMetadataName | none | none |
| AL0646 | warning | WRN_DuplicateParamTag | none | none |
| AL0678 | info | INF_DuplicateMemberMetadataNames | none | none |
| AL0686 | error | ERR_MethodAlreadyDeclaredInBase | none | none |
| AL0687 | error | ERR_IncludedFieldsContainsPrimaryKeyField | none | none |
| AL0690 | error | ERR_PrimaryKeyContainsIncludedFields | none | none |
| AL0699 | error | ERR_OnlySymbolsFromBaseAreAllowed | none | none |
| AL0700 | warning | WRN_ERR_DependencyOnSpecialAppExplicitlyNotAsProperty | none | none |
| AL0701 | error | ERR_DependencyOnSpecialAppExplicitlyNotAsProperty | none | none |
| AL0702 | warning | WRN_ERR_DependencyOnSpecialAppExplicitlyAndAsProperty | none | none |
| AL0703 | error | ERR_DependencyOnSpecialAppExplicitlyAndAsProperty | none | none |
| AL0705 | error | ERR_DuplicateLayoutName | none | none |
| AL0709 | error | ERR_FileDoesNotExist | none | none |
| AL0711 | warning | WRN_ERR_DuplicateMemberNameWithCueAction | none | none |
| AL0712 | error | ERR_DuplicateMemberNameWithCueAction | none | none |
| AL0757 | error | ERR_DuplicateMemberMetadataNames | none | none |
| AL0758 | warning | WRN_ERR_DuplicateMemberMetadataNames | none | none |
| AL0766 | error | ERR_ExternalBusinessEventDuplicateName | none | none |
| AL0790 | warning | WRN_DuplicateUsing | none | none |
| AL0798 | error | ERR_SymbolsCanBeMovedOnlyByFirstPartyApps | none | none |
| AL0803 | warning | WRN_ERR_DuplicateMethodMetadataNames | none | none |
| AL0805 | warning | WRN_ERR_ObjectIdWithQuotesNotSupported | none | none |
| AL0806 | error | ERR_ObjectIdWithQuotesNotSupported | none | none |
| AL0822 | warning | WRN_AmbigSymbolReference | none | none |
| AL0828 | error | ERR_PrimaryKeyFieldCannotBeMoved | none | none |
| AL0829 | error | ERR_SymbolsCannotBeMovedToSameApp | none | none |
| AL0834 | error | ERR_MovedToPropertyIsRequiredForMovedSymbols | none | none |
| AL0835 | warning | WRN_DuplicateLayoutFile | none | none |
| AL0838 | error | ERR_FailedToGenerateTextDataXliffFile | none | none |
| AL0839 | error | ERR_DuplicateTransUnitIdInTextDataXliffFile | none | none |
| AL0841 | error | ERR_DuplicateFileExtension | none | none |
| AL0845 | warning | WRN_ERR_DuplicateEntityNameOrEntitySetName | none | none |
| AL0846 | error | ERR_DuplicateEntityNameOrEntitySetName | none | none |
| AL0862 | error | ERR_DuplicateResourceNames | none | none |
| AL0863 | error | ERR_ResourceFolderDoesNotExist | none | none |
| AL0867 | error | ERR_InterfaceMethodAlreadyDeclaredInExtendedInterface | none | none |
| AL0868 | error | ERR_CannotExtendDueToDuplicateMethods | none | none |
| AL0869 | warning | WRN_UnexpectedSymbolLocation | none | none |
| AL0887 | error | ERR_DuplicateSqlFields | none | none |
| AL0903 | error | ERR_DuplicateDefinitionFile | none | none |
| AL0909 | warning | WRN_MissingAnalysisViewDependency | none | none |
| AL0912 | warning | WRN_ERR_EmptySymbolName | none | none |
| AL0913 | error | ERR_EmptySymbolName | none | none |
| AL0918 | error | ERR_DuplicateInterfaceId | none | none |
| AL1001 | error | ERR_FileNotFound | none | none |
| AL1017 | error | ERR_InvalidManifest | none | none |
| AL1018 | error | ERR_DirectoryNotFound | none | none |
| AL1019 | error | ERR_IncompleteDependency | none | none |
| AL1021 | error | ERR_UnspecifiedPackageCachePath | none | none |
| AL1022 | error | ERR_PackageFileNotFound | none | none |
| AL1023 | error | ERR_InvalidPackageFile | none | none |
| AL1024 | error | ERR_PackageNotLoaded | none | none |
| AL1032 | error | ERR_DuplicateLanguageTranslation | none | none |
| AL1035 | error | ERR_MissingPropertyForTranslationApp | none | none |
| AL1037 | error | ERR_DuplicateLocale | none | none |
| AL1038 | error | ERR_InvalidManifestVersion | none | none |
| AL1039 | error | ERR_InvalidManifestVersion_Short | none | none |
| AL1040 | error | ERR_InvalidManifestGuid | none | none |
| AL1041 | error | ERR_MissingRequiredManifestProperty | none | none |
| AL1042 | error | ERR_ManifestDependencyIdNotMatching | none | none |
| AL1043 | error | ERR_UnsupportedManifestRuntimeVersion | none | none |
| AL1044 | error | ERR_WrongManifestPropertyType | none | none |
| AL1045 | error | ERR_PackageCacheNotFound | none | none |
| AL1048 | error | ERR_DuplicateIdRange | none | none |
| AL1050 | error | ERR_AppFileDoesNotExist | none | none |
| AL1051 | error | ERR_ManifestMismatch | none | none |
| AL1053 | error | ERR_InvalidManifestPropertyValue | none | none |
| AL1056 | warning | WRN_PackageNotLoaded | none | none |
| AL1066 | error | ERR_DuplicatePackageDependency_AppIdPublisherName | none | none |
| AL1067 | error | ERR_DuplicatePackageDependency_PublisherName | none | none |
| AL1068 | error | ERR_DuplicatePackageDependency_AppIdPublisher | none | none |
| AL1069 | error | ERR_DuplicatePackageDependency_AppIdName | none | none |
| AL1070 | error | ERR_DuplicatePackageDependency_AppId | none | none |
| AL1074 | error | ERR_DuplicateAppInsightsResource | none | none |
| AL1076 | info | INF_RenamedDependency | none | none |
| AL1080 | info | INF_IncludeSourceInSymbolFalseApplicableToDev | none | none |
| AL1082 | error | ERR_InvalidManifestPropertyTarget | none | none |
| AL1083 | error | ERR_DuplicateLanguageLCLTranslation | none | none |
| AL1084 | error | ERR_DuplicateLanguageXliffTranslation | none | none |
| AL1085 | warning | WRN_PackageFileLocked | none | none |
| AL1151 | error | ERR_SelfReferenceDependency_NamePublisher | none | none |
| AL1152 | error | ERR_SelfReferenceDependency_AppId | none | none |
| AL1156 | warning | WRN_CommentsInManifestNotRecommended | none | none |
| AL1403 | warning | WRN_PERS_AmbigSymbolReference | none | none |
| AL1408 | warning | WRN_PERS_InvalidApplicationObjectIdentifier | none | none |
| AL1413 | warning | WRN_PERS_DuplicateMemberName | none | none |
| AL1416 | info | INF_PERS_MoveSymbolChangeIgnored | none | none |
| AL1417 | info | INF_PERS_AddSymbolChangeLocationIgnored | none | none |
| AL1429 | warning | WRN_PERS_CannotMoveSymbolsBetweenAreas | none | none |
| AS0001 | error | The {0} with name '{1}' and ID '{2}' was found in the previo | none | model |
| AS0002 | error | The field with name '{0}' and ID '{1}' was found in the prev | none | model |
| AS0003 | error | The version '{0}' of the extension with publisher '{1}', app | none | model |
| AS0004 | error | Field '{0}' has changed type from '{1}' to '{2}'. Type chang | none | model |
| AS0005 | error | The field with ID '{0}' and name '{1}' has been renamed to ' | none | model |
| AS0006 | error | The table with ID '{0}' and name '{1}' has been renamed to ' | none | model |
| AS0007 | error | The {0} with name '{1}' has been moved from namespace '{2}'  | none | model |
| AS0008 | error | The namespace '{0}' is reserved and must be renamed. | none | model |
| AS0009 | error | The field list for key '{0}' has changed from '{1}' to '{2}' | none | model |
| AS0010 | error | The primary key '{0}' has changed from '{1}' to '{2}'. Name  | none | model |
| AS0011 | error | The identifier '{0}' must have at least one of the mandatory | none | model |
| AS0013 | error | The field identifier '{0}' is not valid. It must be within t | none | model |
| AS0014 | error | The project manifest must contain the allocated identifier r | none | model |
| AS0015 | error | The "TranslationFile" flag must be added to the "features" a | none | model |
| AS0016 | error | Field with name '{0}' must use the DataClassification proper | none | model |
| AS0018 | error | Procedure '{0}' has been removed in '{1} {2}'. A procedure t | none | model |
| AS0019 | error | An '{0}' attribute has been removed from '{1}'. This is not  | none | model |
| AS0020 | error | The event attribute cannot be changed from '{0}' to '{1}' on | none | model |
| AS0021 | error | The argument '{0}' for the event attribute '{1}' on '{2}' mu | none | model |
| AS0022 | error | The external scope in '{0}' cannot be removed or changed to  | none | model |
| AS0023 | error | The return type in '{0}' has changed from '{1}' to '{2}'. Th | none | model |
| AS0024 | error | The number of parameters in the external procedure '{0}' has | none | model |
| AS0025 | error | The signature of the event '{0}' has changed from '{1}' to ' | none | model |
| AS0026 | error | The type or subtype of '{0}' has been modified from '{1}' to | none | model |
| AS0027 | error | The array size of a parameter in '{0}' has been modified, th | none | model |
| AS0028 | error | The array size of a parameter in '{0}' has been reduced, thi | none | model |
| AS0029 | error | The '{0}' with ID '{1}' and name '{2}' was found in the prev | none | model |
| AS0030 | error | The '{0}' with ID '{1}' and name '{2}' has been renamed to ' | none | model |
| AS0031 | error | The {0} with name '{1}' defined in {2} '{3}' was found in th | none | model |
| AS0032 | error | The {0} with name '{1}' defined in {2} '{3}' was found in th | none | model |
| AS0033 | error | The {0} with name '{1}' defined in {2} '{3}' was found in th | none | model |
| AS0034 | error | The property '{0}' for {1} '{2}' has changed from value '{3} | none | model |
| AS0035 | warning | The property '{0}' for {1} '{2}' has changed from value '{3} | none | model |
| AS0036 | error | The property '{0}' for field '{1}' in {2} '{3}' has changed  | none | model |
| AS0038 | error | The property '{0}' for key '{1}' in {2} '{3}' has changed fr | none | model |
| AS0039 | error | Property '{0}' has been removed, this is a destructive chang | none | model |
| AS0040 | warning | Property '{0}' has been removed, this is a destructive chang | none | model |
| AS0041 | error | Property '{0}' has been removed, this is a destructive chang | none | model |
| AS0042 | error | Property '{0}' has been removed, this is a destructive chang | none | model |
| AS0043 | error | The clustered key '{0}' has been deleted in {1} '{2}'. Clust | none | model |
| AS0044 | error | OptionMembers has changed value from '{0}' to '{1}', this is | none | model |
| AS0047 | error | The length of the extension name must not exceed 200 charact | none | model |
| AS0048 | error | The length of the extension publisher must not exceed 50 cha | none | model |
| AS0049 | error | The access modifier of the {0} '{1}' cannot be changed to a  | none | model |
| AS0050 | error | The {0} '{1}' was extensible in the previous version of the  | none | model |
| AS0051 | error | The manifest property '{0}' must be specified and contain a  | none | model |
| AS0052 | error | The property 'url' must be set to a valid URL. | none | model |
| AS0053 | error | The compilation target is set to '{0}', but it must be set t | none | model |
| AS0054 | error | The AppSourceCop configuration must specify one of the follo | none | model |
| AS0055 | info | The AppSourceCop configuration must specify the list of coun | none | model |
| AS0056 | warning | The code '{0}' is not a valid ISO 3166-1 alpha-2 code for a  | none | model |
| AS0057 | info | Translations must be provided for the following language cod | none | model |
| AS0058 | error | Only use AssertError in Test Codeunits. | none | model |
| AS0059 | error | The table '{0}' cannot be modified because it is part of the | none | model |
| AS0060 | error | The method '{0}' cannot be invoked in an AppSource applicati | none | model |
| AS0061 | error | Procedure '{0}' cannot subscribe to '{1}' because it can inc | none | model |
| AS0062 | error | {0} '{1}' must have a value for the ApplicationArea property | none | model |
| AS0063 | error | The var modifier has been removed on the parameter '{0}' in  | none | model |
| AS0064 | error | Implementation of interface '{0}' has been deleted on {1} '{ | none | model |
| AS0065 | error | Interface '{0}' has been deleted. | none | model |
| AS0066 | error | Procedure '{0}' has been added in '{1} {2}'. A procedure mus | none | model |
| AS0067 | error | Interface '{0}' has been added to the implemented interfaces | none | model |
| AS0068 | error | The target table of table extension '{0}' has changed from ' | none | model |
| AS0069 | error | The enum '{0}' must have at least the same number of values  | none | model |
| AS0070 | error | The option value '{0}' has been renamed to '{1}' in the enum | none | model |
| AS0071 | error | The enum '{0}' does not declare a value with ordinal value ' | none | model |
| AS0072 | info | The {4} Tag {0} in {1} {2} is not allowed. Expected tag for  | none | model |
| AS0073 | info | The {2} Tag is not set on {0} '{1}'. | none | model |
| AS0074 | info | Found {4} Tag with value '{0}' in the baseline and value '{1 | none | model |
| AS0075 | warning | The {2} Reason is not set on {0} '{1}'. | none | model |
| AS0076 | info | {2} Tag must be formatted {0}. Current Value: {1} | none | model |
| AS0077 | error | A var modifier has been added on the parameter '{0}' in the  | none | model |
| AS0078 | error | A var modifier has been added or removed on the parameter '{ | none | model |
| AS0079 | warning | The procedure '{0}' in {1} '{2}' must have at least one of t | none | model |
| AS0080 | error | Field '{0}' has changed from '{1}' to '{2}' in table or tabl | none | model |
| AS0081 | warning | The InternalsVisibleTo setting will expose your internal obj | none | model |
| AS0082 | error | The enum value with name '{0}' and ID '{1}' defined in '{2}' | none | model |
| AS0083 | error | The enum value with name '{0}' and ID '{1}' was found in the | none | model |
| AS0084 | error | The ID range '{0}' is not valid. It must be within the range | none | model |
| AS0085 | warning | The 'application' property should be used for expressing a d | none | model |
| AS0086 | warning | Field '{0}' has changed from '{1}' to '{2}' in table or tabl | none | model |
| AS0087 | warning | Translations of enum value captions must not contain commas. | none | model |
| AS0088 | error | The '{0}' with ID '{1}' and name '{2}' was found in the prev | none | model |
| AS0089 | error | The '{0}' with name '{1}' was found in the previous version, | none | model |
| AS0090 | error | The '{0}' with ID '{1}' and name '{2}' has been renamed to ' | none | model |
| AS0091 | error | One or more dependencies of the previous version of the exte | none | model |
| AS0092 | warning | The app.json file must specify an Azure Application Insights | none | model |
| AS0094 | warning | The XML file '{0}' should not contain Permissions or Permiss | none | model |
| AS0095 | error | The accessibility of the field '{0}' in {1} '{2}' has change | none | model |
| AS0096 | error | The name of the extension has changed from '{0}' to '{1}'. R | none | model |
| AS0097 | error | The publisher name of the extension has changed from '{0}' t | none | model |
| AS0098 | warning | The identifier '{0}' must have at least one of the mandatory | none | model |
| AS0099 | info | The ID '{0}' for the {1} '{2}' is not valid. It should be wi | none | model |
| AS0100 | error | The 'application' property in the app.json file must be spec | none | model |
| AS0101 | error | The 'Isolated' argument for the event attribute '{0}' on '{1 | none | model |
| AS0102 | error | It is not allowed to add a return value to procedure '{0}' o | none | model |
| AS0103 | warning | Table {0} '{1}' is missing a matching permission set. | none | model |
| AS0104 | error | The extension name '{0}' is not valid. | none | model |
| AS0105 | error | The {0} '{1}' cannot be referenced because it is marked with | none | model |
| AS0106 | error | The variable '{0}' of type '{1}' defined in {2} '{3}' was fo | none | model |
| AS0107 | error | The access modifier of the variable '{0}' of type '{1}' defi | none | model |
| AS0108 | error | The type of variable '{0}' defined in {1} '{2}' has changed  | none | model |
| AS0109 | warning | The type of the table '{0}' has changed from 'Normal' to 'Te | none | model |
| AS0110 | warning | Permissions for the object '{0}' should not be added through | none | model |
| AS0111 | warning | The permission set '{0}' should not be included through a pe | none | model |
| AS0112 | warning | The permission set '{0}' should not be included through a pe | none | model |
| AS0113 | warning | Wildcard permissions should not be included in a permission  | none | model |
| AS0114 | error | The event name cannot be changed from '{0}' to '{1}' because | none | model |
| AS0115 | error | The obsolete state from {0} with name '{1}' has changed from | none | model |
| AS0116 | warning | An extension with AppId '{0}' specified in the 'MovedFrom' p | none | model |
| AS0117 | error | A module with App Id '{0}' that was set in the MovedTo prope | none | model |
| AS0118 | error | Field '{0}' has changed from '{1}' to '{2}' in table or tabl | none | model |
| AS0119 | error | The source symbol '{0}' of type '{1}' with ID '{2}' was foun | none | model |
| AS0120 | error | The destination symbol '{0}' of type '{1}' with ID '{2}' was | none | model |
| AS0121 | error | The name of the moved symbol '{0}' of type '{1}' with ID '{2 | none | model |
| AS0122 | warning | The module with AppId '{0}' specified in the MovedFrom prope | none | model |
| AS0123 | error | The key '{0}' cannot be declared as clustered on an existing | none | model |
| AS0124 | error | The target of the extension object '{0}' has changed from '{ | none | model |
| AS0125 | info | The XLIFF translation ID of the '{0}' '{1}' defined in the ' | none | model |
| AS0126 | warning | The publisher '{0}' defined in the property 'internalsVisibl | none | model |
| AS0127 | warning | Objects should be placed in a namespace with at least two le | none | model |
| AS0128 | error | Interface '{0}' has been removed from list of in extended in | none | model |
| AS0129 | error | Interface '{0}' has been added to list of extended interface | none | model |
| AS0130 | warning | An object of type '{0}' with the same unqualified name '{1}' | none | model |
| AS0131 | info | The {0} with name '{1}' and ID '{2}' was not found in the pr | none | model |
| AS0132 | info | The field with name '{0}' and ID '{1}' was not found in the  | none | model |
| AS0133 | info | The key with name '{0}' was not found in the previous versio | none | model |
| AS0134 | warning | The event version cannot be changed from '{0}' to '{1}' beca | none | model |
| AS0135 | error | One-step removal of the external business event '{0}' is not | none | model |
| AS0136 | warning | The ID of the field '{0}' changed from '{1}' to '{2}'. This  | none | model |
| AS0137 | error | The ID of the field '{0}' changed from '{1}' to '{2}'. This  | none | model |
| AS0138 | info | The field '{0}' should have a value for the AllowInCustomiza | none | model |
| AS0139 | warning | The table field '{0}' must have a value for the AllowInCusto | none | model |
| AS0140 | error | The {0} with name '{1}' defined in {2} '{3}' was found in th | none | model |
| AS0141 | error | The {0} '{1}' with ID '{2}' in app '{3}' appears to have bee | none | model |
| AS0142 | error | The destination {0} '{1}' with ID '{2}' in app '{3}' is miss | none | model |
| AS0146 | warning | The table field '{0}' has been changed from Integer to BigIn | none | model |
| AS0147 | warning | The parameter '{0}' in procedure '{1}' has been changed from | none | model |
| AS0148 | error | Method '{0}' on interface '{1}' was made required without fi | none | model |
| AS0149 | warning | Method '{0}' on interface '{1}' has been {2}. This changes t | none | model |
| AS0150 | error | The object '{0}' must be in a compliant namespace with at le | none | model |
| AS0151 | info | The FullNamespaceScope feature is enabled but mandatory affi | none | model |
| AS0152 | warning | Codeunit '{0}' has been removed but was used as the default  | none | model |
| PTE0001 | error | {0} '{1}' has an ID of [{2}]. It must be within the range '{ | low | model |
| PTE0002 | error | Field '{0}' has an ID of [{1}]. It must be within the range  | low | model |
| PTE0003 | error | Procedure '{0}' cannot subscribe to '{1}' because it can inc | low | model |
| PTE0004 | error | Table {0} '{1}' is missing a matching permission set. | low | model |
| PTE0005 | error | The compilation target is set to '{0}', but it must be set t | low | model |
| PTE0006 | error | Encryption key function '{0}' is not allowed. | low | model |
| PTE0007 | error | Assertion function '{0}' must not be invoked. | low | model |
| PTE0008 | error | {0} '{1}' must have a value for the ApplicationArea property | low | model |
| PTE0009 | error | The app.json '{0}' property must not be used for per-tenant  | low | model |
| PTE0010 | error | The length of the extension name must not exceed 50 characte | low | model |
| PTE0011 | error | The length of the extension publisher must not exceed 50 cha | low | model |
| PTE0012 | warning | The InternalsVisibleTo setting will expose your internal obj | low | model |
| PTE0013 | error | The Entitlement object '{0}' cannot be defined in an extensi | low | model |
| PTE0014 | warning | The XML file '{0}' should not contain Permissions or Permiss | low | model |
| PTE0015 | error | The extension name '{0}' is not valid. | low | model |
| PTE0016 | warning | Permissions for the object '{0}' should not be added through | low | model |
| PTE0017 | warning | The permission set '{0}' should not be included through a pe | low | model |
| PTE0018 | warning | The permission set '{0}' should not be included through a pe | low | model |
| PTE0019 | warning | Wildcard permissions should not be included in a permission  | low | model |
| PTE0020 | warning | The 'application' property should be used for expressing a d | low | model |
| PTE0021 | error | The namespace '{0}' is reserved and must be renamed. | low | model |
| PTE0022 | info | The ID '{0}' for the {1} '{2}' is not valid. It should be wi | low | model |
| PTE0023 | info | The ordinal value '{0} 'for the {1} '{2}' is not valid. It s | low | model |
| PTE0024 | error | '{0}' cannot be moved in a per-tenant extension. | low | model |
| PTE0025 | warning | An object of type '{0}' with the same unqualified name '{1}' | low | model |
| PTE0026 | info | The field '{0}' should have a value for the AllowInCustomiza | low | model |

### obsoletion  (18 codes, 0 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0200 | warning | WRN_PropertyIsObsolete | low | model |
| AL0235 | warning | WRN_EmptyConstIsObsolete | low | model |
| AL0374 | warning | WRN_DeprecatedIdSyntax | low | model |
| AL0424 | warning | WRN_ObsoleteMultilanguageSyntax | low | model |
| AL0432 | warning | WRN_ObsoleteStatePending | low | model |
| AL0433 | error | ERR_ObsoleteStateObsolete | low | model |
| AL0450 | error | ERR_ObsoleteFieldCannotBeUsedInKey | low | model |
| AL0520 | warning | WRN_ObsoleteStateObsolete | low | model |
| AL0601 | warning | WRN_ERR_ObsoleteStateObsolete | low | model |
| AL0667 | warning | WRN_ERR_DeprecatedFeature | low | model |
| AL0691 | error | ERR_PrimaryKeyMustNotBeObsolete | none | none |
| AL0692 | warning | WRN_ERR_PrimaryKeyMustNotBeObsolete | none | none |
| AL0693 | error | ERR_PrimaryKeyFieldMustNotBeObsolete | none | none |
| AL0694 | warning | WRN_ERR_PrimaryKeyFieldMustNotBeObsolete | none | none |
| AL0797 | error | ERR_ObsoleteStateMoved | low | model |
| AL0801 | warning | WRN_ObsoleteStatePendingMove | low | model |
| AL1412 | warning | WRN_PERS_ObsoleteStatePending | low | model |
| AL1415 | warning | WRN_PERS_ObsoleteStateObsolete | low | model |

### other  (3 codes, 0 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL-0001 | warning | Unknown | low | model |
| AL-0002 | warning | Void | low | model |
| AL0000 | warning | None | low | model |

### permission  (14 codes, 0 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0195 | error | ERR_InvalidPermissionValue | none | none |
| AL0251 | warning | WRN_PermissionObjectIsMissing | none | none |
| AL0393 | error | ERR_PermissionDuplicatedObject | none | none |
| AL0415 | error | ERR_AccessibilityModifierNotAllowed | none | none |
| AL0651 | error | ERR_PermissionSetCircularReference | low | model |
| AL0652 | error | ERR_PermissionSetSelfReference | none | none |
| AL0679 | warning | WRN_MissingObjectEntitlement | none | none |
| AL0683 | error | ERR_ObjectEntitlementFromOtherModule | none | none |
| AL0684 | warning | WRN_ObjectEntitlementContainsFromOtherModule | none | none |
| AL0732 | error | ERR_AccessModifierNotAllowedInContext | none | none |
| AL0733 | warning | WRN_ERR_AccessModifierNotAllowedInContext | none | none |
| AL0740 | error | ERR_PermissionSetIncludedExcludeSamePermissionSet | none | none |
| AL0741 | error | ERR_PermissionSetSelfReferenceExclude | none | none |
| AL0776 | error | ERR_IdentifierIsNotAPermissionValue | none | none |

### semantic  (623 codes, 16 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0108 | error | ERR_IndexersMustHaveAtLeastOneValue | medium | model |
| AL0112 | error | ERR_InvalidAttribute | medium | model |
| AL0113 | error | ERR_AtLeastOneDimension | medium | model |
| AL0116 | error | ERR_InvalidPropertyOptionValue | high | model |
| AL0120 | error | ERR_LocalIllegallyOverrides | medium | model |
| AL0124 | error | ERR_PropertyInfoNotAvailable | medium | model |
| AL0131 | error | ERR_CharAllowedFormatIsWrong | medium | model |
| AL0133 | error | ERR_BadArgType | medium | model |
| AL0135 | error | ERR_NoCorrespondingArgument | medium | model |
| AL0136 | error | ERR_ForLoopVariableMustBeNumeric | medium | model |
| AL0137 | error | ERR_NoBreak | medium | model |
| AL0138 | error | ERR_ArrayNotValidForCase | medium | model |
| AL0139 | error | ERR_ExitValueNotAllowed | medium | model |
| AL0140 | error | ERR_ExpressionNotValidForWith | medium | model |
| AL0142 | error | ERR_TemporaryMustBeTable | medium | model |
| AL0143 | error | ERR_BadIndexLHS | medium | model |
| AL0144 | error | ERR_BadIndexCount | medium | model |
| AL0145 | error | ERR_ArrayNotValidForAssign | medium | model |
| AL0146 | error | ERR_ArrayIsTooBig | medium | model |
| AL0147 | error | ERR_ArrayDimensionMustBePositiveNumber | medium | model |
| AL0148 | error | ERR_InvalidTableFilter | medium | model |
| AL0149 | error | ERR_ElseWithoutIf | medium | model |
| AL0150 | error | ERR_InvalidConstExpression | medium | model |
| AL0151 | error | ERR_LeftMustBeOption | medium | model |
| AL0153 | error | ERR_PropertyCannotBeBlank | medium | model |
| AL0154 | error | ERR_FieldLengthTooBig | medium | model |
| AL0156 | error | ERR_InvalidFieldType | medium | model |
| AL0157 | error | ERR_InvalidVariableType | medium | model |
| AL0158 | error | ERR_InvalidParameterType | medium | model |
| AL0159 | error | ERR_InvalidReturnType | medium | model |
| AL0160 | error | ERR_InvalidLanguageId | medium | model |
| AL0161 | error | ERR_BadAccess | medium | model |
| AL0163 | error | ERR_InvalidTriggerSignature | medium | model |
| AL0165 | error | ERR_TriggersCannotBeCalledDirectly | medium | model |
| AL0166 | error | ERR_BadArgMember | medium | model |
| AL0169 | error | ERR_InvalidOptionValue | medium | model |
| AL0171 | error | ERR_InvalidPropertyValue | high | analyzer-codefix |
| AL0173 | error | ERR_BadUnaryOp | medium | model |
| AL0175 | error | ERR_BadBinaryOps | medium | model |
| AL0176 | error | ERR_InvalidCalculationFormulaMethod | medium | model |
| AL0181 | error | ERR_InvalidFilterExpression | medium | model |
| AL0184 | error | ERR_InvalidPropertyExpression | medium | model |
| AL0185 | error | ERR_MissingApplicationObject | medium | model |
| AL0186 | error | ERR_MissingTypeReference | medium | model |
| AL0187 | error | ERR_AttributeAllowedOnlyOn | medium | model |
| AL0189 | error | ERR_MutuallyExclusiveAttributes | medium | model |
| AL0192 | error | ERR_ReturnValueMustBeUsed | medium | model |
| AL0193 | error | ERR_BadArgTypeMustBeSameAsFirstArgument | medium | model |
| AL0199 | error | ERR_InvalidSumIndexKeyType | medium | model |
| AL0201 | error | ERR_FlowFieldMustBeBoolean | medium | model |
| AL0202 | error | ERR_FlowFieldMustBeInteger | medium | model |
| AL0203 | error | ERR_SumAverageOnlySupportedForNumericFields | medium | model |
| AL0207 | error | ERR_ExpressionMustBeTextType | medium | model |
| AL0208 | error | ERR_ExpressionMustBeBooleanType | medium | model |
| AL0211 | error | ERR_InvalidAreaKind | medium | model |
| AL0213 | error | ERR_AreaOnlyValidOnPageOfType | medium | model |
| AL0214 | error | ERR_FactBoxesNotAllowedOnParts | medium | model |
| AL0215 | error | ERR_PartsCannotContainParts | medium | model |
| AL0216 | error | ERR_FactBoxesCanOnlyContainParts | medium | model |
| AL0217 | error | ERR_OnlyGroupsAndPartsAreValidInRoleCenters | medium | model |
| AL0221 | error | ERR_ValueOutsideValidRange | medium | model |
| AL0229 | error | ERR_InvalidExtendedDataTypeRatio | medium | model |
| AL0230 | error | ERR_RequiresTextualExtendedDataType | medium | model |
| AL0232 | error | ERR_PropertyValueMustBePositive | medium | model |
| AL0236 | error | ERR_EmptyConstIsNotSupported | medium | model |
| AL0238 | error | ERR_BadAttributeArgCount | medium | model |
| AL0240 | error | ERR_ParameterTypeDoesNotMatchAttribute | medium | model |
| AL0241 | error | ERR_ParameterCountDoesNotMatchAttribute | medium | model |
| AL0242 | error | ERR_InvalidAttributeArgumentSyntax | medium | model |
| AL0243 | error | ERR_BadAttributeCodeunitSubtype | medium | model |
| AL0244 | error | ERR_ReturnValueTypeDoesNotMatchAttribute | medium | model |
| AL0245 | error | ERR_VisibilityDoesNotMatchAttribute | medium | model |
| AL0246 | error | ERR_NonCustomizableProperty | high | model |
| AL0250 | error | ERR_RequiresMediaExtendedDataType | medium | model |
| AL0254 | warning | WRN_SortingFieldShouldBePartOfKey | low | model |
| AL0255 | error | ERR_RequiresApplicationObjectRunObject | medium | model |
| AL0256 | error | ERR_FlowFieldCannotBePartOfKeys | medium | model |
| AL0259 | error | ERR_SqlIndexOnPKMustBeIdentical | medium | model |
| AL0262 | error | ERR_ClusteredKeyCanAppearOnce | medium | model |
| AL0267 | error | ERR_ActionsAreNotAllowedOnThisControlType | medium | model |
| AL0268 | error | ERR_GroupingOfActionsNotAllowed | medium | model |
| AL0269 | warning | WRN_ERR_PagePartMustBePart | low | model |
| AL0272 | error | ERR_AnchorMustBeGroupType | medium | model |
| AL0273 | warning | WRN_ERR_ReuseOfAreaName | low | model |
| AL0274 | error | ERR_AnchorCannotBeArea | medium | model |
| AL0279 | error | ERR_TableKeyTooManyFields | medium | model |
| AL0281 | error | ERR_MemberNotAnEvent | medium | model |
| AL0282 | error | ERR_EventUnmatchedParameter | medium | model |
| AL0283 | error | ERR_EventReturnNotValid | medium | model |
| AL0285 | error | ERR_EventPublisherIncludeSenderWithParameterSender | medium | model |
| AL0286 | error | ERR_EventPublisherCannotContainCode | medium | model |
| AL0287 | error | ERR_EventPublisherCannotContainVariables | medium | model |
| AL0288 | error | ERR_EventParameterByVarIsNotAllowed | medium | model |
| AL0290 | error | ERR_EventElementNameShouldBeEmpty | medium | model |
| AL0291 | error | ERR_EventTriggerEventPageMissingSourceTable | medium | model |
| AL0293 | error | ERR_PropertyValueNotAValidOptionValue | medium | model |
| AL0298 | error | ERR_InvalidStyleExpressionPropertyValue | medium | model |
| AL0299 | warning | WRN_ERR_MemberNameOnlyAllowedForTriggers | low | model |
| AL0300 | error | ERR_PropertyUsedAsMethod | high | model |
| AL0301 | error | ERR_ListCannotEndWithSeparator | medium | model |
| AL0302 | error | ERR_UseBeforeDeclaration | medium | model |
| AL0304 | error | ERR_IdentifierTooLong | medium | model |
| AL0306 | error | ERR_FieldListCannotBeEmpty | medium | model |
| AL0307 | error | ERR_SourceTableUnreachable | medium | model |
| AL0309 | error | ERR_TableTooManyKeys | medium | model |
| AL0310 | error | ERR_ObjectRequired | medium | model |
| AL0311 | error | ERR_ObjectProhibited | medium | model |
| AL0313 | error | ERR_AttributeOnlyAllowedIn | high | model |
| AL0314 | error | ERR_PropertyOnlyValidInControlOfType | medium | model |
| AL0315 | error | ERR_ControlNotInGroup | medium | model |
| AL0316 | error | ERR_ExpressionMustBeIntegerType | medium | model |
| AL0318 | error | ERR_InvalidRunObjectPropertyValue | high | model |
| AL0319 | error | ERR_MissingTargetsForMove | medium | model |
| AL0320 | error | ERR_PageMustSpecifySourceTable | medium | model |
| AL0321 | error | ERR_InvalidInDatasetDatatype | medium | model |
| AL0322 | error | ERR_InvalidInClientExpression | medium | model |
| AL0323 | error | ERR_InvalidSystemPartKind | medium | model |
| AL0324 | error | ERR_LanguageSpecifiedMoreThanOnce | medium | model |
| AL0325 | error | ERR_FieldTypeCannotBeUsedInKey | medium | model |
| AL0326 | error | ERR_InvalidColumnType | high | model |
| AL0327 | error | ERR_MissingDocument | medium | model |
| AL0329 | error | ERR_WordMergeDataItemMustBeTopLevel | medium | model |
| AL0331 | error | ERR_TopLevelDataItemCannotHaveLinkProperty | medium | model |
| AL0332 | error | ERR_InvalidControlType | medium | model |
| AL0333 | error | ERR_InvalidFieldAccessSyntax | medium | model |
| AL0334 | error | ERR_ExtensionCannotBeDeclared | medium | model |
| AL0335 | error | ERR_AttributesMustBeNestedInsideElements | high | model |
| AL0336 | error | ERR_ThereMustBeOneRootNode | medium | model |
| AL0337 | error | ERR_MissingTableElement | medium | model |
| AL0338 | error | ERR_EventTriggerEventPageMissingSourceTableButFilled | medium | model |
| AL0340 | error | ERR_InvalidRoleCenterPage | medium | model |
| AL0342 | error | ERR_UnionsAreNotSupportedInQueries | medium | model |
| AL0343 | error | ERR_QueriesMustHaveTopLevelDataItem | medium | model |
| AL0344 | error | ERR_DataItemLinkMustBeSetForNestedDataItems | medium | model |
| AL0345 | error | ERR_QueryElementSourceMustBeFieldOnTable | medium | model |
| AL0346 | error | ERR_DateMethodsIncompatibleWithQueryColumnType | medium | model |
| AL0347 | error | ERR_AggregationMethodsIncompatibleWithQueryColumnType | medium | model |
| AL0349 | error | ERR_MissingColumnReference | medium | model |
| AL0351 | error | ERR_DataItemLinkMustReferenceFieldOnAncestorDataItem | medium | model |
| AL0352 | error | ERR_QueriesMustDefineAtLeastOneColumn | medium | model |
| AL0353 | error | ERR_QueryColumnsMustDefineSourceExpressionOrCountMethod | medium | model |
| AL0354 | error | ERR_CannotMoveRelativeToItself | medium | model |
| AL0355 | error | ERR_CannotMoveMultipleTimes | medium | model |
| AL0356 | error | ERR_CannotModifyMultipleTimes | medium | model |
| AL0357 | error | ERR_CannotAddMultipleTimes | medium | model |
| AL0358 | error | ERR_CannotMoveOrModifyInTheSameExtensionYouAdded | medium | model |
| AL0359 | error | ERR_InvalidXmlName | medium | model |
| AL0360 | error | ERR_TextLiteralNotProperlyTerminated | medium | model |
| AL0361 | error | ERR_IdentifierNotProperlyTerminated | medium | model |
| AL0362 | error | ERR_PathMustBeRelative | medium | model |
| AL0363 | error | ERR_PathSeperatorIsNotValidOnCurrentOs | medium | model |
| AL0364 | error | ERR_OptionReferencedAsMember | medium | model |
| AL0365 | error | ERR_PropertyValuesAreMutuallyExclusive | medium | model |
| AL0366 | error | ERR_TableHasToHaveAtLeastOneNormalField | medium | model |
| AL0367 | error | ERR_ArrayMustHaveAtLeastOneDimension | medium | model |
| AL0368 | error | ERR_ArrayTooManyDimensions | medium | model |
| AL0369 | error | ERR_ConstOutOfRange | medium | model |
| AL0370 | error | ERR_DivByZero | medium | model |
| AL0371 | error | ERR_CheckedOverflow | medium | model |
| AL0372 | error | ERR_ConstantStringTooLong | medium | model |
| AL0373 | error | ERR_XmlNameMustBeSpecified | medium | model |
| AL0375 | error | ERR_OptionCannotContainComma | medium | model |
| AL0376 | error | ERR_ControlTypeNotAllowedInParent | medium | model |
| AL0377 | error | ERR_InvalidAttributeValueForVariableType | medium | model |
| AL0378 | error | ERR_RoleCenterShouldNotHaveTriggers | medium | model |
| AL0379 | error | ERR_NameIsNotValidClsIdentifier | medium | model |
| AL0385 | error | ERR_IncludeCaptionCannotBeSetForNonField | medium | model |
| AL0388 | error | ERR_DateFormulaSignMissing | medium | model |
| AL0389 | error | ERR_DateFormulaNumberOutOfRange | medium | model |
| AL0390 | error | ERR_DateFormulaShouldIncludeQuantor | medium | model |
| AL0391 | error | ERR_DateFormulaShouldIncludeANumber | medium | model |
| AL0392 | error | ERR_DateFormulaValueTooLong | medium | model |
| AL0396 | error | ERR_CannotHaveMethodsOnPageCustomization | medium | model |
| AL0397 | error | ERR_ColumnNameFormatClash | medium | model |
| AL0398 | error | ERR_ConstantValueNotAValidOptionValue | medium | model |
| AL0399 | error | ERR_CannotHaveVariablesOnPageCustomization | medium | model |
| AL0401 | error | ERR_MultiplePageCustomizationsSpecifiedPerProfilePerTargetPage | medium | model |
| AL0403 | error | ERR_ModifyContainsNoChange | medium | model |
| AL0404 | error | ERR_PropertyInvalidOnTableExtension | medium | model |
| AL0406 | error | ERR_InvalidTypeForSomething | medium | model |
| AL0407 | error | ERR_GenericTypeArgumentCountMismatch | medium | model |
| AL0408 | error | ERR_InvalidTypeArgument | medium | model |
| AL0409 | error | ERR_TypeIsNotGeneric | medium | model |
| AL0410 | error | ERR_NoRequestPage | medium | model |
| AL0412 | error | ERR_NotAllowedSyntax | medium | model |
| AL0413 | error | ERR_MethodBodyNotAllowed | medium | model |
| AL0414 | error | ERR_MethodBodyMustBeSpecified | medium | model |
| AL0416 | error | ERR_ReturnValueNotAllowed | medium | model |
| AL0418 | error | ERR_ControlAddWrongLinkFormat | medium | model |
| AL0419 | error | ERR_EventSubscriberMissingParameter | medium | model |
| AL0420 | error | ERR_VarParameterNotAllowed | medium | model |
| AL0421 | error | ERR_ForEachExpressionMustBeEnumerable | medium | model |
| AL0422 | error | ERR_InvalidApiVersionId | medium | model |
| AL0423 | error | ERR_PropertyCanBeUsedOnlyOnKeysWithFieldsFromTheSameTable | medium | model |
| AL0425 | error | ERR_InvalidCodeunitSubtypeForTrigger | medium | model |
| AL0427 | error | ERR_CalcFormulaConversionError | medium | model |
| AL0428 | error | ERR_CannotSpecifyPropertiesAtTheSameTime | medium | model |
| AL0429 | error | ERR_RepeaterCanOnlyBeAddedToPagesThatHaveASourceTable | medium | model |
| AL0430 | error | ERR_ParameterTypeNotSerializable | medium | model |
| AL0436 | error | ERR_PropertyValueCannotBeEmpty | medium | model |
| AL0437 | error | ERR_EmptyListMember | medium | model |
| AL0438 | error | ERR_ValueTypeDoesNotMatchFieldType | medium | model |
| AL0439 | error | ERR_InvalidLabelProperty | medium | model |
| AL0440 | error | ERR_MethodAlreadyExists | medium | model |
| AL0441 | error | ERR_EventTriggerPageParameterMissingSourceTable | medium | model |
| AL0442 | error | ERR_EventTriggerPageParameterMissingSourceTableButFilled | medium | model |
| AL0443 | error | ERR_InvalidSystemObject | medium | model |
| AL0444 | error | ERR_MalformedReportLayout | medium | model |
| AL0445 | error | ERR_FileInUse | medium | model |
| AL0447 | error | ERR_PropertyValueCannotBeUsedInThisContext | medium | model |
| AL0448 | error | ERR_MemberNotAllowedInContext | medium | model |
| AL0451 | error | ERR_DotNetAssemblyCouldNotBeFound | medium | model |
| AL0452 | error | ERR_DotNetTypeCouldNotBeFound | medium | model |
| AL0453 | error | ERR_ExperimentalFeatureDisabled | medium | model |
| AL0454 | error | ERR_ExtensionTargetTypeCannotBeExtended | medium | model |
| AL0455 | error | ERR_InvalidOptionOrdinalValue | medium | model |
| AL0456 | error | ERR_InvalidNumberOfOptionOrdinalValues | medium | model |
| AL0457 | warning | WRN_IncorrectLabelSyntax | low | model |
| AL0458 | error | ERR_InvalidAttributeForVariableType | medium | model |
| AL0459 | error | ERR_AttributeCanOnlyBeSpecifiedOnGlobalVariables | medium | model |
| AL0460 | error | ERR_ClientSideEventsAreSupportedOnlyOnPages | medium | model |
| AL0461 | error | ERR_InvalidDotNetEventPublisher | medium | model |
| AL0463 | error | ERR_EventParameterByVarMismatch | medium | model |
| AL0465 | error | ERR_ExternalResourceNotAllowed | medium | model |
| AL0466 | error | ERR_FileIsReadonly | medium | model |
| AL0467 | warning | WRN_FileIsReadonly | low | model |
| AL0468 | warning | WRN_ERR_FieldNameIdentifierTooLong | high | model |
| AL0470 | error | ERR_HeadlinePartMustUsedInRoleCenter | medium | model |
| AL0471 | error | ERR_WrongLinkFormat | medium | model |
| AL0472 | warning | WRN_TranslationItemSourceStringMismatch | low | model |
| AL0473 | warning | WRN_TranslationItemTranslatedStringTooLong | low | model |
| AL0474 | error | ERR_AttributeCanOnlyBeSpecifiedOnLocalVariables | medium | model |
| AL0475 | error | ERR_AttributeCannotBeUsedOnVariablesOfArrayType | medium | model |
| AL0480 | error | ERR_AttributesCannotHaveNestedElements | medium | model |
| AL0481 | warning | WRN_ERR_FieldImageOnlyOnFieldInCueGroup | low | model |
| AL0482 | warning | WRN_ImageNotValid | high | model |
| AL0483 | warning | WRN_ImageOnNestedActionGroupInSectionsArea | low | model |
| AL0484 | error | ERR_InvalidAlphaNumeric | medium | model |
| AL0485 | error | ERR_MissingMandatoryPropertyObjectOfTypeAPI | medium | model |
| AL0487 | error | ERR_FieldWithInvalidFieldClassAsIndexField | medium | model |
| AL0492 | error | ERR_ActionAreaShouldOnlyRunListPages | medium | model |
| AL0493 | warning | WRN_ERR_ActionAreaShouldOnlyRunListPages | low | model |
| AL0494 | error | ERR_ActionAreaShouldOnlyContainGroups | medium | model |
| AL0496 | error | ERR_AttributeContext | medium | model |
| AL0498 | error | ERR_AttributeCanOnlyBeUsedOnProceduresWithAttribute | medium | model |
| AL0499 | error | ERR_MissingHandlerFunction | medium | model |
| AL0500 | error | ERR_HandlerFunctionsListShouldNotHaveSpaces | medium | model |
| AL0501 | error | ERR_TestCodeunitsEventSubscribersMustHaveManualBinding | medium | model |
| AL0502 | error | ERR_LinkTableValueMustReferenceTableElement | medium | model |
| AL0504 | error | ERR_EnumNotExtensible | medium | model |
| AL0505 | error | ERR_ApiPageShouldHaveDelayedInsert | medium | model |
| AL0506 | error | ERR_AreaShouldOnlyContainGroups | medium | model |
| AL0509 | warning | WRN_ConstantValueNotAValidOptionValue | medium | model |
| AL0510 | error | ERR_DotNetTypeIsNotControlAddIn | medium | model |
| AL0511 | error | ERR_DotNetTypeDeclarationDoesNotContainIsControlAddInProperty | medium | model |
| AL0517 | error | ERR_InvalidHelpLinkProperty | medium | model |
| AL0519 | error | ERR_InvalidValueInContext | medium | model |
| AL0522 | error | ERR_PropertyValueNotAValidEnumValue | medium | model |
| AL0523 | warning | WRN_ERR_MethodAlreadyExists | low | model |
| AL0525 | error | ERR_SystemTableCannotBeExtended | medium | model |
| AL0526 | error | ERR_ApiPageCouldOnlyBePartOfAnotherApiPage | medium | model |
| AL0527 | error | ERR_SqlTimestampFieldCannotBePartOfKeys | medium | model |
| AL0528 | error | ERR_ApiPageFieldsShouldHaveAlphaNumericName | medium | model |
| AL0529 | error | ERR_ApiQueryColumnsShouldHaveAlphaNumericName | medium | model |
| AL0530 | error | ERR_TypeLengthTooBig | medium | model |
| AL0531 | error | ERR_ApiPageAndSubpagePropertyMismatch | medium | model |
| AL0532 | error | ERR_ApiPagePartAndSubpagePropertyMismatch | medium | model |
| AL0534 | warning | WRN_ERR_KeyNameIdentifierTooLong | low | model |
| AL0535 | error | ERR_ApiPagePartMustBePartOrApi | medium | model |
| AL0536 | error | ERR_AddChangeNotSupportedForViews | medium | model |
| AL0537 | error | ERR_ViewsOnlySupportedOnPagesOfType | medium | model |
| AL0538 | error | ERR_ViewsOrderByOnlySupportOneDirection | medium | model |
| AL0540 | error | ERR_InvalidViewName | medium | model |
| AL0541 | error | ERR_ViewsBooleanExpressionsShouldNotUseVariables | medium | model |
| AL0542 | error | ERR_PropertyNotAllowedOnPageWithoutSourceTable | high | model |
| AL0544 | error | ERR_ContextSentiveHelpWithPlaceholder | medium | model |
| AL0545 | warning | WRN_ERR_AreaNotValidOnPageOfType | low | model |
| AL0546 | error | ERR_ViewsLayoutOnlySupportedOnContent | medium | model |
| AL0547 | warning | WRN_ERR_EventPublisherCannotExposeGlobalVariables | low | model |
| AL0549 | error | ERR_CannotHaveMethodsOnPageViews | medium | model |
| AL0550 | warning | WRN_ERR_ActionAreaGroupShouldOnlyContainActions | low | model |
| AL0551 | warning | WRN_ERR_ActionAreaShouldOnlyContainActions | low | model |
| AL0552 | warning | WRN_ERR_ActionAreaShouldOnlyContainGroups | low | model |
| AL0553 | error | ERR_CannotAddActionsOfTypeFromPageCustomization | medium | model |
| AL0555 | error | ERR_ActionAreaShouldOnlyRunObjectsOfType | medium | model |
| AL0556 | warning | WRN_ERR_ActionAreaShouldOnlyRunObjectsOfType | low | model |
| AL0557 | warning | WRN_CodeunitLocalVariableShadowingTableField | low | model |
| AL0558 | warning | WRN_CodeunitGlobalvariableHasSameNameAsTableField | low | model |
| AL0559 | warning | WRN_ERR_PartsCannotContainParts | low | model |
| AL0560 | warning | WRN_ERR_OnlyGroupsAndPartsAreValidInRoleCenters | low | model |
| AL0561 | warning | WRN_ERR_FactBoxesCanOnlyContainParts | low | model |
| AL0562 | warning | WRN_ERR_InvalidSystemPartKind | low | model |
| AL0563 | warning | WRN_ERR_ControlTypeNotAllowedInParent | low | model |
| AL0564 | error | ERR_ObjectNotExtensible | medium | model |
| AL0567 | warning | WRN_TableFieldShadowingSystemField | low | model |
| AL0568 | warning | WRN_ERR_ActionAreaGroupShouldOnlyContainActionsOrGroups | low | model |
| AL0569 | warning | WRN_ERR_RoleCenterShouldNotHaveProcedures | low | model |
| AL0570 | error | ERR_TranslationIdDuplication | medium | model |
| AL0571 | warning | WRN_ERR_UseCaptionPropertyForProfile | low | model |
| AL0572 | error | ERR_GenericIOError | medium | model |
| AL0573 | warning | WRN_ERR_InvalidInClientExpression | low | model |
| AL0574 | error | ERR_ObjectNotAllowedForExtensionDevelopment | medium | model |
| AL0575 | error | ERR_CannotReferenceElementDefinedInPageCustomization | medium | model |
| AL0576 | error | ERR_InvalidProfileName | medium | model |
| AL0577 | error | ERR_ViewWithLayoutChangesMustHaveSharedLayout | medium | model |
| AL0578 | error | ERR_InvalidLabelPropertyValue | medium | model |
| AL0579 | error | ERR_InvalidMultilanguagePropertyValue | medium | model |
| AL0580 | error | ERR_SynthesizedFieldCannotBeUsedInKey | medium | model |
| AL0581 | error | ERR_TypeLengthMustBePositive | medium | model |
| AL0582 | error | ERR_InterfaceRequiredMemberMissing | medium | model |
| AL0584 | error | ERR_InterfaceMemberCantHaveVarSection | medium | model |
| AL0585 | error | ERR_InterfaceCantHaveVarSection | medium | model |
| AL0588 | warning | WRN_EventSubscriberParameterEnumToOption | low | model |
| AL0590 | warning | WRN_ERR_PropertyMustBeSetOnGroupKind | low | model |
| AL0591 | error | ERR_PropertyMustBeSetOnGroupKind | medium | model |
| AL0592 | warning | WRN_CompatibilityReason | low | model |
| AL0593 | warning | WRN_ERR_EventSubscriberParameterTypeLossyConversion | low | model |
| AL0594 | error | ERR_XmlSerializationErrorOccurred | medium | model |
| AL0595 | error | ERR_InterfaceIsNotImplementedByObj | medium | model |
| AL0596 | error | ERR_InterfaceIsNotImplementedByEnumValueOrDefaultImplementation | medium | model |
| AL0598 | warning | WRN_ERR_CannotMoveOrModifyInTheSameExtensionYouAdded | low | model |
| AL0600 | warning | WRN_ERR_RelaxedOptionRelatedProperty | low | model |
| AL0602 | warning | WRN_ERR_BadAccess | low | model |
| AL0603 | warning | WRN_DangerousImplicitConversion | high | model |
| AL0604 | warning | WRN_ERR_UseOfImplicitWith | low | model |
| AL0605 | warning | HDN_UseOfImplicitWith | low | model |
| AL0606 | warning | WRN_ERR_UseOfExplicitWith | medium | model |
| AL0607 | warning | HDN_UseOfExplicitWith | low | model |
| AL0608 | warning | WRN_ERR_OrderByWithoutFields | low | model |
| AL0609 | warning | WRN_AddingActionCueGroup | low | model |
| AL0610 | warning | WRN_MovingActionCueGroup | low | model |
| AL0611 | warning | WRN_ModifyActionCueGroup | low | model |
| AL0612 | error | ERR_InterfaceMemberMustBeDeclareMethod | medium | model |
| AL0613 | warning | WRN_ERR_InvalidTriggerSignature | low | model |
| AL0614 | warning | WRN_ERR_ReservedPropertyValue | low | model |
| AL0615 | warning | WRN_ERR_ODataKeyFieldNotReferenced | low | model |
| AL0616 | error | ERR_ReservedCodeunitInterfaceMethodSignature | medium | model |
| AL0617 | warning | WRN_ERR_OnBeforeActionEventNotValidWithRunObject | low | model |
| AL0619 | error | ERR_CaptionAttributeNotServiceProcedure | medium | model |
| AL0620 | error | ERR_BadDirectivePlacement | medium | model |
| AL0625 | error | ERR_PPDefFollowsToken | medium | model |
| AL0627 | warning | WRN_IllegalPPWarning | low | model |
| AL0628 | warning | WRN_IllegalPragma | low | model |
| AL0629 | error | ERR_InvalidPreprocExpr | medium | model |
| AL0630 | error | ERR_IllegalEscape | medium | model |
| AL0633 | warning | WRN_IllegalPPImplicitWith | low | model |
| AL0635 | warning | WRN_ERR_EventSubscriberWithOnPremAttribute | low | model |
| AL0636 | error | ERR_RequiresBigTextExtendedDataType | medium | model |
| AL0637 | error | ERR_NavigationMustBeOnAPIPage | medium | model |
| AL0638 | error | ERR_VariantAsReportColumn | medium | model |
| AL0639 | warning | WRN_ERR_VariantAsReportColumn | low | model |
| AL0640 | warning | WRN_XMLParseError | low | model |
| AL0641 | warning | WRN_MissingParamTag | low | model |
| AL0642 | warning | WRN_MissingXMLComment | low | model |
| AL0643 | warning | WRN_UnprocessedXMLComment | low | model |
| AL0644 | warning | WRN_UnmatchedParamTag | low | model |
| AL0645 | warning | WRN_UnmatchedParamRefTag | low | model |
| AL0647 | warning | WRN_ErrorOverride | low | model |
| AL0648 | error | ERR_OpenEndedComment | medium | model |
| AL0649 | warning | WRN_ERR_CommaInEnumValue | low | model |
| AL0650 | warning | WRN_ERR_TranslationSourceStringTooLong | low | model |
| AL0653 | error | ERR_IdSyntaxNotAllowed | medium | model |
| AL0654 | error | ERR_PropertyWrongFileExtension | medium | model |
| AL0655 | warning | WRN_ERR_DataItemLinkMustReferenceParent | low | model |
| AL0656 | error | ERR_CannotAnchorControlsAddedInTheSameExtension | medium | model |
| AL0657 | error | ERR_MissingMandatoryPropertyOfPartOfTypeAPI | medium | model |
| AL0658 | error | ERR_MemberNameOnlyAllowedForTriggers | medium | model |
| AL0659 | warning | WRN_EnumIdentifierTooLong | low | model |
| AL0660 | warning | WRN_ERR_NonCustomizableProperty | high | model |
| AL0662 | warning | WRN_BigIntegerNarrowingConversionInProperty | low | model |
| AL0663 | warning | WRN_BigIntegerNarrowingConversionInPropertyToEnum | low | model |
| AL0665 | error | ERR_ReturnTypeIsNotSupportedForVersion | medium | model |
| AL0666 | error | ERR_FeatureNotAvailable | medium | model |
| AL0668 | error | ERR_FeatureNotSupportedOnCrossPlatformBuilds | medium | model |
| AL0671 | error | ERR_DeletedObjectChangeFoundInCompilation | medium | model |
| AL0672 | error | ERR_DataItemTableFilterOnNonNormalField | medium | model |
| AL0673 | error | ERR_RequiredProperty | medium | model |
| AL0674 | error | ERR_ConditionalRequiredProperty | medium | model |
| AL0675 | error | ERR_InterfaceIsAlreadyImplemented | medium | model |
| AL0676 | error | ERR_ProtectedMemberNotAllowedForObject | medium | model |
| AL0677 | warning | WRN_ERR_ProtectedMemberNotAllowedForObject | low | model |
| AL0680 | error | ERR_CannotAddNewTopLevelDataItem | medium | model |
| AL0685 | warning | WRN_ERR_CalcFormulaTargetCannotBeLargerThanSourceField | low | model |
| AL0688 | error | ERR_IncludedFieldsContainsKeyField | medium | model |
| AL0689 | error | ERR_IncludedFieldsContainsSqlIndexField | medium | model |
| AL0695 | warning | WRN_ERR_MethodCannotBeUsedInThisContext | low | model |
| AL0696 | error | ERR_ArgumentShouldBeFieldType | medium | model |
| AL0697 | warning | WRN_ERR_ArgumentShouldBeFieldType | low | model |
| AL0698 | error | ERR_InvalidCaseOfType | medium | model |
| AL0704 | error | ERR_EmptyDefaultExcelLayout | medium | model |
| AL0706 | error | ERR_LegacyLayoutProperty | medium | model |
| AL0707 | error | ERR_LayoutFilenameInvalidExtension | medium | model |
| AL0708 | error | ERR_InvalidMimeType | medium | model |
| AL0710 | error | ERR_InvalidDefaultLayout | medium | model |
| AL0713 | error | ERR_ControlAddInEventsShouldBeImplementedAsTriggers | medium | model |
| AL0714 | error | ERR_ReuseOfAreaName | medium | model |
| AL0715 | warning | WRN_ERR_ReservedName | low | model |
| AL0716 | error | ERR_ReservedName | medium | model |
| AL0717 | warning | WRN_MissingCalcFormulaOnFlowField | low | model |
| AL0718 | error | ERR_InvalidReportLayoutName | medium | model |
| AL0719 | info | INF_ArgumentShouldBeFieldType | none | none |
| AL0721 | error | ERR_DefaultRenderingLayoutMustBeSpecified | medium | model |
| AL0722 | error | ERR_PropertyNotAllowedForActionsV2 | high | model |
| AL0723 | error | ERR_ActionTypeNotAllowedForActionRef | medium | model |
| AL0724 | error | ERR_AreaNotValidOnPageOfType | medium | model |
| AL0725 | error | ERR_ActionTypeIsNotSupportedInArea | medium | model |
| AL0730 | error | ERR_InvalidSumIndexField | medium | model |
| AL0734 | error | ERR_PropertyValueInvalidGuid | medium | model |
| AL0735 | error | ERR_CustomActionCannotBeUsedWithPromotedActionProperties | medium | model |
| AL0736 | error | ERR_InvalidFlowEnvironmentIdPropertyValue | medium | model |
| AL0737 | error | ERR_ActionRefOrPromotedGroupCannotBeReferenedWhenUsingPromotedActionSyntax | medium | model |
| AL0738 | error | ERR_EmptyMemberName | medium | model |
| AL0739 | warning | WRN_EmptyMemberName | low | model |
| AL0742 | error | ERR_InvalidPropertyForActionInControlOfType | medium | model |
| AL0743 | warning | WRN_ERR_InvalidPropertyForActionInControlOfType | low | model |
| AL0744 | error | ERR_InvalidPropertyForRequestPage | medium | model |
| AL0745 | warning | WRN_ERR_InvalidPropertyForRequestPage | low | model |
| AL0746 | error | ERR_AutoIncrementFieldCanOnlyAppearOnce | medium | model |
| AL0747 | error | ERR_RequiresNonConstTextualType | medium | model |
| AL0748 | warning | WRN_PublicMethodReturnValueExposingInternalTypes | none | none |
| AL0749 | warning | WRN_PublicMethodParameterExposingInternalTypes | none | none |
| AL0750 | error | ERR_CantNestEnumValues | medium | model |
| AL0751 | warning | WRN_ERR_CantNestEnumValues | low | model |
| AL0752 | error | ERR_EmptyDataitemName | medium | model |
| AL0753 | warning | WRN_ERR_EmptyDataitemName | low | model |
| AL0754 | error | ERR_BuiltInMemberAlreadyExists | medium | model |
| AL0755 | warning | WRN_ERR_BuiltInMemberAlreadyExists | low | model |
| AL0756 | warning | WRN_DivisionByAbsWillChangeItsBehaviour | low | model |
| AL0759 | error | ERR_InvalidFormatRegion | medium | model |
| AL0760 | error | ERR_UnsupportedFormatRegion | medium | model |
| AL0761 | error | ERR_ExternalBusinessEventCategoryInvalideEnum | medium | model |
| AL0762 | error | ERR_ArgumentTooLong | medium | model |
| AL0763 | error | ERR_InvalidAlphanumericArgument | medium | model |
| AL0764 | error | ERR_EmptyArgument | medium | model |
| AL0765 | error | ERR_ExternalBusinessEventMethodArgumentType | medium | model |
| AL0767 | error | ERR_ExternalRulesetPathNotAllowed | medium | model |
| AL0768 | warning | WRN_ERR_ConditionalRequiredProperty | low | model |
| AL0769 | warning | WRN_ERR_RequiredProperty | low | model |
| AL0772 | error | ERR_ConditionalAttribute | medium | model |
| AL0773 | warning | WRN_ExceedsNumberOfFiles | low | model |
| AL0774 | error | ERR_TryFunctionDiscardsExitValues | medium | model |
| AL0775 | warning | WRN_ERR_TryFunctionDiscardsExitValues | low | model |
| AL0777 | error | ERR_OverflowInGuidConversion | medium | model |
| AL0778 | warning | WRN_ERR_OverflowInGuidConversion | low | model |
| AL0779 | error | ERR_CannotModifyAllFlowfield | medium | model |
| AL0780 | warning | WRN_ERR_CannotModifyAllFlowfield | low | model |
| AL0781 | error | ERR_CannotFindDataItemToLink | medium | model |
| AL0782 | warning | WRN_ERR_CannotAccessForeignControlAddInFromPageExtension | low | model |
| AL0783 | error | ERR_CannotAccessForeignControlAddInFromPageExtension | medium | model |
| AL0784 | error | ERR_ExternalBusinessEventVersionMalformed | medium | model |
| AL0785 | error | ERR_ControlKindNotSupportedInPageCustomization | medium | model |
| AL0786 | error | ERR_PropertyKindNotSupportedInPageCustomization | medium | model |
| AL0787 | error | ERR_SourceExpressionKindNotSupportedInPageCustomization | medium | model |
| AL0788 | warning | WRN_ERR_AreaOnlyValidOnPageOfType | low | model |
| AL0789 | warning | WRN_UsingWithoutNamespace | low | model |
| AL0792 | warning | HDN_UnusedUsing | low | model |
| AL0793 | error | ERR_PropertyNotAllowedForMutliSelectAction | high | model |
| AL0794 | error | ERR_InvalidPropertyValueForActionInControlOfType | high | model |
| AL0795 | error | ERR_SecretTextParametersNotAllowedOnEvents | medium | model |
| AL0796 | warning | WRN_SecretTextUnwrapShouldBeUsedInsideNonDebuggableMethod | medium | model |
| AL0799 | error | ERR_SourceTableFieldCannotBeUsedInCustomization | medium | model |
| AL0800 | error | ERR_CertainEDTNotAllowedOnTableField | medium | model |
| AL0802 | error | ERR_SecretTextParametersNotAllowedOnControlAddInProcedures | medium | model |
| AL0804 | warning | WRN_ERR_CannotReferenceElementDefinedInPageCustomization | low | model |
| AL0807 | warning | WRN_ObjectNameShouldNotBeInteger | low | model |
| AL0808 | error | ERR_CannotSetPropertyValueInPageCustomization | medium | model |
| AL0809 | error | ERR_SecretTextCannotBeProtectedVar | medium | model |
| AL0810 | error | ERR_InvalidSystemActionName | medium | model |
| AL0811 | error | ERR_InvalidSystemActionTrigger | medium | model |
| AL0812 | error | ERR_PromptOptionsAreaCanOnlyContainOptionFields | medium | model |
| AL0813 | error | ERR_DependentPropertyValueNotSupported | medium | model |
| AL0814 | warning | WRN_ERR_QueryElementSourceMustNotBeFlowFilter | low | model |
| AL0815 | error | ERR_QueryElementSourceMustNotBeFlowFilter | medium | model |
| AL0816 | warning | WRN_ERR_PropertyValuesAreMutuallyExclusive | low | model |
| AL0817 | error | ERR_ControlNotValidOnAreaForPageOfType | medium | model |
| AL0818 | warning | WRN_ERR_EventAlreadyExists | low | model |
| AL0819 | error | ERR_EventAlreadyExists | medium | model |
| AL0820 | warning | WRN_MissingApplicationObject | low | model |
| AL0821 | warning | WRN_InvalidAddActionMethod | low | model |
| AL0823 | warning | WRN_MovedFieldCannotBeUsedInKey | low | model |
| AL0824 | error | ERR_MovedFieldCannotBeUsedInKey | medium | model |
| AL0825 | error | ERR_FieldCannotBeMovedToBaseTable | medium | model |
| AL0826 | warning | WRN_ERR_InvalidTypeArgument | low | model |
| AL0827 | error | ERR_FieldClassNotAllowed | medium | model |
| AL0830 | warning | WRN_ERR_TryFunctionCannotBeUsedAsImplementation | low | model |
| AL0831 | error | ERR_TryFunctionCannotBeUsedAsImplementation | medium | model |
| AL0832 | error | ERR_ActionAreaNotValidOnControlOfType | medium | model |
| AL0833 | error | ERR_ActionNotAllowedInContext | medium | model |
| AL0836 | warning | WRN_BaseTableFieldFromSameAppExtensionReference | low | model |
| AL0837 | warning | WRN_ERR_TranslationIdDuplication | low | model |
| AL0840 | error | ERR_InvalidFileExtension | medium | model |
| AL0842 | warning | WRN_PublicFieldExposingInternalTypes | none | none |
| AL0843 | error | ERR_PropertyUnsupportedAssociatedTypeSingleValue | medium | model |
| AL0844 | error | ERR_PropertyUnsupportedAssociatedTypeMultipleValues | medium | model |
| AL0848 | warning | WRN_IdentifierIsKeywordFromVersion | low | model |
| AL0849 | error | ERR_CannotReferencePageCustomizationWithClearPropertiesFromProfileExtension | medium | model |
| AL0850 | error | ERR_FeatureOnlyAllowedForMicrosoft | medium | model |
| AL0851 | error | ERR_TypeCanNotBeCast | medium | model |
| AL0852 | error | ERR_InterfaceCircularReference | medium | model |
| AL0853 | error | ERR_PagePartCircularReference | medium | model |
| AL0855 | error | ERR_VariableNameCannotBeEmpty | medium | model |
| AL0856 | error | ERR_StatementCannotStartWithParen | medium | model |
| AL0857 | error | ERR_ResourceFileTooLarge | medium | model |
| AL0858 | error | ERR_ResourceFilesTooLarge | medium | model |
| AL0859 | error | ERR_ResourceFileHasInvalidExtension | medium | model |
| AL0860 | error | ERR_ResourcePathTooLong | medium | model |
| AL0861 | error | ERR_TooManyResources | medium | model |
| AL0864 | warning | WRN_ERR_ChartPartNotSupported | low | model |
| AL0865 | error | ERR_ChartPartNotSupported | medium | model |
| AL0866 | error | ERR_ResourceIsEmpty | medium | model |
| AL0871 | error | ERR_IllegalAtSequence | medium | model |
| AL0873 | error | ERR_NoContinue | medium | model |
| AL0874 | error | ERR_UserControlHost_ExpectsSingleUserControlWithinContent | medium | model |
| AL0875 | error | ERR_UserControlHost_ActionsNotSupported | medium | model |
| AL0876 | error | ERR_IncompatiblePropertySingleValue | medium | model |
| AL0877 | error | ERR_IncompatiblePropertyMultipleValues | medium | model |
| AL0878 | error | ERR_IncompatibleProperty | medium | model |
| AL0879 | error | ERR_TriggerRestrictedByAssociatedProperty | medium | model |
| AL0880 | error | ERR_TriggerRestrictedByAssociatedPropertySingleValue | medium | model |
| AL0881 | error | ERR_TriggerRestrictedByAssociatedPropertyMultipleValues | medium | model |
| AL0882 | error | ERR_UserControlHost_ExpectsSingleTextFieldWithinNavigation | medium | model |
| AL0883 | error | ERR_TestHttpResponseMessage_InvalidHttpStatusCode | medium | model |
| AL0884 | error | ERR_TestHttpResponseMessage_NotAllowedHttpStatusCode | medium | model |
| AL0885 | warning | WRN_ERR_OnlyFieldsFromBaseAreAllowed | low | model |
| AL0886 | error | ERR_OnlyFieldsFromBaseAreAllowed | medium | model |
| AL0888 | warning | WRN_SecretPotentiallyExposedToBrowser | low | model |
| AL0889 | error | ERR_ReservedKeywordName | medium | model |
| AL0890 | error | ERR_InvalidSystemPartIdentifier | medium | model |
| AL0891 | error | ERR_UnsupportedExtendedDataType | medium | model |
| AL0892 | error | ERR_InvalidExtendedDataTypeFieldReference | medium | model |
| AL0893 | error | ERR_NativeMethodCannotContainCode | medium | model |
| AL0894 | error | ERR_NativeMethodCannotContainVariables | medium | model |
| AL0895 | error | ERR_NativeMethodOnlyInMSRange | medium | model |
| AL0896 | error | ERR_RecursiveFlowfieldNotAllowed | medium | model |
| AL0898 | error | ERR_AnalysisViewsOnlySupportedOnPagesOfType | medium | model |
| AL0900 | error | ERR_DefinitionFilenameInvalidExtension | medium | model |
| AL0901 | error | ERR_DefinitionFileIsMalformed | medium | model |
| AL0902 | error | ERR_AnalysisViewTargetObjectMismatch | medium | model |
| AL0904 | error | ERR_MissingRequiredAnalysisViewProperty | medium | model |
| AL0906 | warning | WRN_ConfigurationDialogPublicPreview | low | model |
| AL0907 | error | ERR_ConfigurationDialogUnsupportedStartCard | medium | model |
| AL0908 | error | ERR_RequiresBigIntegerExtendedDataType | medium | model |
| AL0910 | warning | WRN_ERR_FlowFieldCannotBeUsedInQueryDataItemLink | low | model |
| AL0911 | error | ERR_FlowFieldCannotBeUsedInQueryDataItemLink | medium | model |
| AL0914 | warning | WRN_TableHasTooManyFields | low | model |
| AL0915 | warning | WRN_TableExtensionHasTooManyFields | low | model |
| AL0919 | error | ERR_ScopeNotAllowedOnInterfaceMember | medium | model |
| AL0920 | warning | WRN_ERR_InternalMethodCannotImplementInterface | none | none |
| AL0921 | error | ERR_InternalMethodCannotImplementInterface | none | none |
| AL0922 | error | ERR_OnPremMethodCannotImplementInterface | medium | model |
| AL0923 | error | ERR_RequiredPendingOnNonDefaultMethod | medium | model |
| AL0924 | warning | WRN_InterfaceRequiredPendingMemberMissing | low | model |
| AL0925 | info | INF_InterfaceOptionalMemberMissing | none | none |
| AL0926 | error | ERR_SectionOutOfOrder | medium | model |
| AL0929 | error | ERR_InvalidDefaultHeaderFooterPart | medium | model |
| AL0930 | error | ERR_InvalidDefaultThemePart | medium | model |
| AL0931 | error | ERR_InvalidObjectReference | medium | model |
| AL0999 | error | ERR_InternalError | none | none |
| AL1000 | warning | WRN_NoConfigNotOnCommandLine | low | model |
| AL1002 | error | ERR_OpenResponseFile | medium | model |
| AL1003 | warning | WRN_AnalyzerCannotBeCreated | low | model |
| AL1004 | warning | WRN_NoAnalyzerInAssembly | low | model |
| AL1005 | warning | WRN_UnableToLoadAnalyzer | low | model |
| AL1006 | error | ERR_NoMetadataFile | medium | model |
| AL1007 | error | ERR_NoFileSpec | medium | model |
| AL1008 | error | ERR_SwitchNeedsString | medium | model |
| AL1009 | error | ERR_BadSwitch | medium | model |
| AL1010 | error | ERR_SwitchNeedsNumber | medium | model |
| AL1011 | warning | WRN_FileAlreadyIncluded | low | model |
| AL1012 | error | ERR_OutputWriteFailed | medium | model |
| AL1013 | error | ERR_BinaryFile | medium | model |
| AL1014 | error | ERR_NoSourceFile | medium | model |
| AL1015 | error | ERR_CompileCanceled | medium | model |
| AL1025 | warning | WRN_FileDoesNotMatchAnyFormat | low | model |
| AL1026 | warning | WRN_XmlValidationErrorOccurred | low | model |
| AL1028 | error | ERR_IOExceptionCaught | medium | model |
| AL1029 | warning | WRN_TranslationFileTargetLanguageInvalid | low | model |
| AL1030 | warning | WRN_TranslationFileTargetLanguageMissing | low | model |
| AL1031 | info | INF_SuccessfullyIncludedTranslationsForLanguages | none | none |
| AL1033 | error | ERR_InvalidRuleSetInclude | medium | model |
| AL1034 | error | ERR_HelpUrlWithMissingLocalePlaceHolders | medium | model |
| AL1036 | error | ERR_InvalidTranslationLocaleCulture | medium | model |
| AL1046 | error | ERR_ApplicationIdRangesAreOverlapping | medium | model |
| AL1047 | error | ERR_InvalidApplicationIdRanges | medium | model |
| AL1049 | error | ERR_OutputFileNotSpecified | medium | model |
| AL1052 | error | ERR_HelpUrlWithTooManyPlaceHolders | medium | model |
| AL1054 | error | ERR_InvalidReferenceModule | medium | model |
| AL1055 | warning | WRN_InvalidReferenceModule | low | model |
| AL1057 | error | ERR_InvalidModuleSpecification | medium | model |
| AL1058 | warning | WRN_AppIdAndIdBothSpecified | low | model |
| AL1059 | warning | WRN_RequiredFeature | low | model |
| AL1060 | error | ERR_InvalidMaxDegreeOfParallelism | medium | model |
| AL1061 | error | ERR_NavAppFilesValidationError | medium | model |
| AL1062 | error | ERR_KeyVaultUrls_TooManySpecified | medium | model |
| AL1063 | error | ERR_KeyVaultUrls_TooLongUrl | medium | model |
| AL1064 | error | ERR_KeyVaultUrls_InvalidAzureKeyVaultUri | medium | model |
| AL1065 | error | ERR_KeyVaultUrls_PathOrQueryStringAllowed | medium | model |
| AL1071 | error | ERR_DocFileGen | medium | model |
| AL1072 | warning | WRN_DefineIdentifierRequired | low | model |
| AL1073 | error | ERR_ClashesWithDeclaredTrigger | medium | model |
| AL1075 | error | ERR_BothShowMyCodeAndResourceExposurePolicyExist | medium | model |
| AL1077 | error | ERR_FailedToLoadWorkspace | medium | model |
| AL1078 | warning | WRN_ERR_KeyVaultUrls_InvalidAzureKeyVaultUri | low | model |
| AL1079 | info | INF_AllowDebuggingFalseApplicableToDev | none | none |
| AL1081 | error | ERR_ReportLayoutUpdateFailure | medium | model |
| AL1100 | warning | FTL_InputFileNameTooLong | low | model |
| AL1101 | warning | FTL_InvalidTarget | low | model |
| AL1130 | error | ERR_InvalidTimeoutDuration | medium | model |
| AL1150 | error | ERR_InvalidLink | medium | model |
| AL1153 | error | ERR_InvalidReferenceModuleVersion | medium | model |
| AL1154 | error | ERR_ConflictingCommandLineArguments | medium | model |
| AL1155 | error | ERR_NoFolderSpec | medium | model |
| AL1401 | warning | WRN_PERS_MissingTypeReference | low | model |
| AL1402 | warning | WRN_PERS_MissingApplicationObject | low | model |
| AL1407 | warning | WRN_PERS_MissingTargetsForMove | low | model |
| AL1409 | warning | WRN_PERS_InvalidRoleCenterPage | low | model |
| AL1411 | warning | WRN_PERS_MultiplePageCustomizationsSpecifiedPerProfilePerTargetPage | low | model |
| AL1414 | info | INF_PERS_CustomizationWithoutChanges | none | none |
| AL1420 | warning | WRN_PERS_ActionTypeNotAllowedForActionRef | low | model |
| AL1421 | warning | WRN_PERS_PromotedActionUsage | low | model |
| AL1425 | warning | WRN_PERS_SourceTableFieldCannotBeUsedInCustomization | low | model |
| AL1427 | warning | WRN_PERS_CannotSetPropertyValueInPageCustomization | low | model |
| AL1430 | warning | WRN_SortingFieldFromAnotherExtensionNotInKey | low | model |

### syntax  (49 codes, 47 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0104 | error | ERR_SyntaxError | high | deterministic |
| AL0105 | error | ERR_IdentifierExpectedKW | high | deterministic |
| AL0106 | error | ERR_ForStatementToOrDownToExpected | high | deterministic |
| AL0107 | error | ERR_IdentifierExpected | high | model |
| AL0109 | error | ERR_UnexpectedToken | high | deterministic |
| AL0110 | error | ERR_OrphanedElseStatement | high | deterministic |
| AL0111 | error | ERR_SemicolonExpected | high | deterministic |
| AL0114 | error | ERR_IntegerLiteralExpected | high | deterministic |
| AL0115 | error | ERR_ObjectTypeExpected | high | deterministic |
| AL0117 | error | ERR_IllegalStatement | medium | model |
| AL0125 | error | ERR_MethodNameExpected | medium | deterministic |
| AL0128 | error | ERR_LanguageIdExpected | high | deterministic |
| AL0129 | error | ERR_AssgLvalueExpected | high | deterministic |
| AL0130 | error | ERR_RefLvalueExpected | high | deterministic |
| AL0170 | error | ERR_EqualExpected | high | deterministic |
| AL0178 | error | ERR_ExpectedFilterKeywordOrIdentifier | high | deterministic |
| AL0179 | error | ERR_ExpectedIdentifierOrMemberAccess | high | deterministic |
| AL0180 | error | ERR_ExpectedFilterKeyword | high | deterministic |
| AL0182 | error | ERR_ExpectedIdentifierOrLiteral | high | deterministic |
| AL0183 | error | ERR_UnexpectedCharacter | high | deterministic |
| AL0198 | error | ERR_ExpectedApplicationObjectKeyword | high | model |
| AL0218 | error | ERR_ExpectedIntLiteral | high | deterministic |
| AL0219 | error | ERR_ExpectedStringLiteral | high | deterministic |
| AL0220 | error | ERR_ExpectedBooleanLiteral | high | deterministic |
| AL0224 | error | ERR_ExpressionExpected | high | deterministic |
| AL0252 | error | ERR_ExpectedAscendingOrDescendingKeyword | high | deterministic |
| AL0276 | error | ERR_ExpectedTimeLiteral | high | deterministic |
| AL0277 | error | ERR_ExpectedDateLiteral | high | deterministic |
| AL0278 | error | ERR_ExpectedDateTimeLiteral | high | deterministic |
| AL0292 | error | ERR_ExpectedFieldFilterOrConstKeyword | high | deterministic |
| AL0405 | error | ERR_ExpectedOptionValue | high | deterministic |
| AL0434 | error | ERR_ExpectedNumericLiteral | high | deterministic |
| AL0435 | error | ERR_ExpectedLiteral | high | deterministic |
| AL0489 | error | ERR_PropertyExpressionKindIsNotValidExpectedConstOrFilter | high | deterministic |
| AL0490 | error | ERR_PropertyExpressionKindIsNotValidExpectedConstOrFieldOrFilter | high | deterministic |
| AL0491 | error | ERR_PropertyExpressionKindIsNotValidExpectedAllExpressionKind | high | deterministic |
| AL0621 | error | ERR_PPDirectiveExpected | high | deterministic |
| AL0622 | error | ERR_EndRegionDirectiveExpected | high | deterministic |
| AL0623 | error | ERR_EndifDirectiveExpected | high | deterministic |
| AL0624 | error | ERR_UnexpectedDirective | high | deterministic |
| AL0626 | warning | WRN_IdentifierOrNumericLiteralExpected | high | deterministic |
| AL0631 | error | ERR_EndOfPPLineExpected | high | deterministic |
| AL0632 | error | ERR_CloseParenExpected | high | deterministic |
| AL0634 | warning | WRN_EndOfPPLineExpected | high | deterministic |
| AL0726 | error | ERR_ExpectedIdentifierOrLiteralOrOptionAccess | high | deterministic |
| AL0854 | error | ERR_UnexpectedNamespace | high | deterministic |
| AL0870 | error | ERR_ExpectedVerbatimLiteral | high | deterministic |
| AL0917 | warning | WRN_ExcelLayoutOrphanedSheet | high | deterministic |
| AL0927 | error | ERR_ExpectedSystemObject | high | deterministic |

### type  (10 codes, 8 high-likelihood)

| code | sev | enum / title | halluc | fix |
|---|---|---|---|---|
| AL0122 | error | ERR_NoImplicitConversion | high | model |
| AL0126 | error | ERR_BadArgCount | high | model |
| AL0127 | error | ERR_NonInvocableMemberCalled | high | model |
| AL0172 | error | ERR_AmbigUnaryOp | medium | model |
| AL0174 | error | ERR_AmbigBinaryOps | high | model |
| AL0204 | error | ERR_FieldTypeMismatch | medium | model |
| AL0284 | error | ERR_EventSubscriberParameterTypeMismatch | high | model |
| AL0294 | error | ERR_PropertyTypeFieldTypeMismatch | high | model |
| AL0382 | error | ERR_AmbiguosOptionAccess | high | model |
| AL0916 | warning | WRN_AmbiguousBuiltInMethodCall | high | model |

## Ranked: codes an AL-writing LLM most commonly hits

Drives the G5 mutation catalog and G7 auto-fix work.

| # | code | category | template | g5_mutation | fix_strategy |
|---|---|---|---|---|---|
| 1 | AL0104 | syntax | Syntax error, '{0}' expected | delete_token | deterministic |
| 2 | AL0105 | syntax | Syntax error, identifier expected; '{1}' is a keyword | rename_identifier_to_keyword | deterministic |
| 3 | AL0106 | syntax | Syntax error, 'TO' or 'DOWNTO' expected | delete_token | deterministic |
| 4 | AL0107 | syntax | Syntax error, identifier expected. Provide a valid name (letters, digi | rename_identifier_to_keyword | model |
| 5 | AL0109 | syntax | Unexpected token encountered. Check syntax for missing operators, keyw | insert_stray_token | deterministic |
| 6 | AL0110 | syntax | Orphaned ELSE statement. This is most likely because of an unnecessary | semicolon_before_else | deterministic |
| 7 | AL0111 | syntax | Semicolon expected. Add a semicolon (;) to terminate the statement. | delete_semicolon | deterministic |
| 8 | AL0114 | syntax | Syntax error, integer literal expected. Provide a numeric value (e.g., | delete_token | deterministic |
| 9 | AL0115 | syntax | Object type expected. Valid types include: Table, Page, Report, Codeun | delete_token | deterministic |
| 10 | AL0116 | semantic | Invalid value for '{0}'. Allowed values are '{1}' | — | model |
| 11 | AL0118 | binding | The name '{0}' does not exist in the current context. | rename_identifier | model |
| 12 | AL0122 | type | Cannot implicitly convert type '{0}' to '{1}'. Use an explicit convers | change_var_type | model |
| 13 | AL0126 | type | No overload for method '{0}' takes {1} arguments. Candidates: {2} | swap_argument_count | model |
| 14 | AL0127 | type | Member '{0}' cannot be used like a method. Remove the parentheses or c | add_parens_to_property | model |
| 15 | AL0128 | syntax | Language identifier expected (e.g., 'ENU', 'DEU', or an LCID). | delete_token | deterministic |
| 16 | AL0129 | syntax | The left-hand side of an assignment must be a variable or field | delete_token | deterministic |
| 17 | AL0130 | syntax | A 'var' argument must be an assignable variable (field, variable, or p | delete_token | deterministic |
| 18 | AL0132 | binding | '{0}' does not contain a definition for '{1}' | rename_member | model |
| 19 | AL0134 | binding | '{0}' is not recognized as a valid type. Verify the type name is corre | rename_type | model |
| 20 | AL0162 | binding | '{0}' is not a valid trigger for this object type. Check the object do | rename_trigger | model |
| 21 | AL0167 | binding | The {0} '{1}' can only be used if the property '{2}' is set with any o | rename_identifier | model |
| 22 | AL0168 | binding | The {0} '{1}' can only be used if the property '{2}' is set | rename_identifier | model |
| 23 | AL0170 | syntax | An '=' is expected for property {0}. Use the format: PropertyName = Va | delete_token | deterministic |
| 24 | AL0171 | semantic | The property value '{0}' on property '{1}' is not valid. | corrupt_property_value | analyzer-codefix |
| 25 | AL0174 | type | Operator '{0}' is ambiguous on operands of type '{1}' and '{2}' | operator_type_misuse | model |
| 26 | AL0178 | syntax | A 'FILTER' keyword or an identifier is expected in the filter expressi | delete_token | deterministic |
| 27 | AL0179 | syntax | An identifier or a member access expression is expected (e.g., 'FieldN | delete_token | deterministic |
| 28 | AL0180 | syntax | A 'FILTER' keyword is expected in this context. Use FILTER(...) to spe | delete_token | deterministic |
| 29 | AL0182 | syntax | An identifier or a literal is expected as the value of a filter expres | delete_token | deterministic |
| 30 | AL0183 | syntax | Unexpected character '{0}'. Remove the invalid character or check if a | delete_token | deterministic |
| 31 | AL0198 | syntax | Expected one of the application object keywords ({0}) | drop_var_declaration | model |
| 32 | AL0218 | syntax | An integer literal value is expected for property {0} | delete_token | deterministic |
| 33 | AL0219 | syntax | Syntax error, string literal expected. Enclose the text in single quot | delete_token | deterministic |
| 34 | AL0220 | syntax | Syntax error, boolean literal expected. Use 'true' or 'false'. | delete_token | deterministic |
| 35 | AL0223 | binding | The {0} '{1}' can only be used if the property '{2}' is set to '{3}' | rename_identifier | model |
| 36 | AL0224 | syntax | Expression expected. Provide a valid expression (variable, constant, c | delete_token | deterministic |
| 37 | AL0246 | semantic | The property '{0}' cannot be customized. This property is read-only in | — | model |
| 38 | AL0247 | binding | The target {0} '{1}' for the extension object is not found | rename_object_ref | model |
| 39 | AL0252 | syntax | Expected 'Ascending' or 'Descending' value. | delete_token | deterministic |
| 40 | AL0270 | binding | The control '{0}' is not found in the target '{1}' | rename_control_ref | model |
