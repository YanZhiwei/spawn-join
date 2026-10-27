@{
    # High-signal rules only; CLI scripts intentionally use Write-Host and positional
    # native arguments, so style rules for those are excluded.
    IncludeRules = @(
        'PSAvoidGlobalVars'
        'PSAvoidUsingConvertToSecureStringWithPlainText'
        'PSAvoidUsingInvokeExpression'
        'PSAvoidUsingPlainTextForPassword'
        'PSAvoidUsingUsernameAndPasswordParams'
        'PSPossibleIncorrectComparisonWithNull'
        'PSPossibleIncorrectUsageOfAssignmentOperator'
        'PSReviewUnusedParameter'
        'PSUseApprovedVerbs'
        'PSUseCompatibleSyntax'
        'PSUseDeclaredVarsMoreThanAssignments'
    )
    Rules = @{
        PSUseCompatibleSyntax = @{
            Enable = $true
            TargetVersions = @('7.0')
        }
    }
}
