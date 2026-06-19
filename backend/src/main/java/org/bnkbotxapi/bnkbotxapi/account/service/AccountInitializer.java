package org.bnkbotxapi.bnkbotxapi.account.service;

import lombok.RequiredArgsConstructor;
import org.bnkbotxapi.bnkbotxapi.account.domain.AccountEntity;
import org.bnkbotxapi.bnkbotxapi.account.domain.AccountRole;
import org.bnkbotxapi.bnkbotxapi.account.repository.AccountRepository;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class AccountInitializer implements ApplicationRunner {

    private final AccountRepository accountRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(ApplicationArguments args) {
        saveIfMissing("admin", "admin123", "관리자", AccountRole.ADMIN);
        saveIfMissing("employee", "employee123", "은행직원", AccountRole.BANK_EMPLOYEE);
    }

    private void saveIfMissing(String loginId, String password, String name, AccountRole role) {
        if (accountRepository.existsByLoginId(loginId)) {
            return;
        }
        accountRepository.save(AccountEntity.builder()
                .loginId(loginId)
                .password(passwordEncoder.encode(password))
                .name(name)
                .role(role)
                .build());
    }
}
