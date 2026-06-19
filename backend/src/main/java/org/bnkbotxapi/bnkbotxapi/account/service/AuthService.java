package org.bnkbotxapi.bnkbotxapi.account.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.log4j.Log4j2;
import org.bnkbotxapi.bnkbotxapi.account.domain.AccountEntity;
import org.bnkbotxapi.bnkbotxapi.account.dto.AccountReadDTO;
import org.bnkbotxapi.bnkbotxapi.account.dto.LoginRequestDTO;
import org.bnkbotxapi.bnkbotxapi.account.dto.LoginResponseDTO;
import org.bnkbotxapi.bnkbotxapi.account.repository.AccountRepository;
import org.bnkbotxapi.bnkbotxapi.common.exception.CommonExceptions;
import org.bnkbotxapi.bnkbotxapi.security.auth.CustomUserPrincipal;
import org.bnkbotxapi.bnkbotxapi.security.util.JWTUtil;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Log4j2
@Transactional
@RequiredArgsConstructor
public class AuthService {

    private final AccountRepository accountRepository;
    private final PasswordEncoder passwordEncoder;
    private final JWTUtil jwtUtil;

    public LoginResponseDTO login(LoginRequestDTO request) {
        AccountEntity account = accountRepository.findByLoginIdAndDeletedFalse(request.getLoginId())
                .orElseThrow(() -> CommonExceptions.BAD_AUTH.get());

        if (!passwordEncoder.matches(request.getPassword(), account.getPassword())) {
            throw CommonExceptions.BAD_AUTH.get();
        }

        String accessToken = jwtUtil.makeAccessToken(account);
        String refreshToken = jwtUtil.makeRefreshToken(account);
        account.setRefreshToken(refreshToken);

        return toLoginResponse(account, accessToken, refreshToken);
    }

    public LoginResponseDTO refresh(String refreshToken) {
        jwtUtil.validate(refreshToken);
        AccountEntity account = accountRepository.findByRefreshTokenAndDeletedFalse(refreshToken)
                .orElseThrow(() -> CommonExceptions.BAD_AUTH.get());

        String newAccessToken = jwtUtil.makeAccessToken(account);
        String newRefreshToken = jwtUtil.makeRefreshToken(account);
        account.setRefreshToken(newRefreshToken);

        return toLoginResponse(account, newAccessToken, newRefreshToken);
    }

    public void logout(CustomUserPrincipal principal) {
        accountRepository.findById(principal.getAccountId()).ifPresent(account -> {
            account.setRefreshToken(null);
            accountRepository.save(account);
        });
    }

    public AccountReadDTO me(CustomUserPrincipal principal) {
        return AccountReadDTO.builder()
                .accountId(principal.getAccountId())
                .loginId(principal.getUsername())
                .name(principal.getName())
                .role(principal.getRole().name())
                .build();
    }

    private LoginResponseDTO toLoginResponse(AccountEntity account, String accessToken, String refreshToken) {
        return LoginResponseDTO.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .accountId(account.getAccountId())
                .loginId(account.getLoginId())
                .name(account.getName())
                .role(account.getRole().name())
                .build();
    }
}
